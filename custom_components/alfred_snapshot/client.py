"""Small independent Alfred snapshot client; no browser automation."""
import asyncio
import base64
import json
import time
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape, quoteattr
import aiohttp

API = "https://api.my-alfred.com"
C = "jabber:client"
F = "urn:ietf:params:xml:ns:xmpp-framing"
S = "urn:ietf:params:xml:ns:xmpp-sasl"
B = "urn:ietf:params:xml:ns:xmpp-bind"
class AuthError(Exception): pass
class ProtocolError(Exception): pass

def varint(n):
    b=bytearray()
    while n>127:
        b.append((n&127)|128); n>>=7
    b.append(n)
    return bytes(b)
def integer(k,v): return varint(k<<3)+varint(v)
def blob(k,v): return varint(k<<3|2)+varint(len(v))+v

def fields(data):
    i=0; out={}
    def read():
        nonlocal i
        v=0
        for shift in range(0,70,7):
            if i>=len(data): raise ProtocolError("Truncated varint")
            b=data[i];i+=1;v|=(b&127)<<shift
            if b<128:return v
        raise ProtocolError("Invalid varint")
    while i<len(data):
        tag=read();k,w=tag>>3,tag&7
        if not k:raise ProtocolError("Invalid field")
        if w==0:v=read()
        elif w in (1,2,5):
            n=read() if w==2 else (8 if w==1 else 4)
            if i+n>len(data):raise ProtocolError("Truncated field")
            v=data[i:i+n];i+=n
        else:raise ProtocolError("Unsupported wire type")
        out[k]=v
    return out

def request():
    return integer(2,1)+integer(3,2)+integer(4,1)+blob(6,integer(1,640)+integer(2,360))

def session_from_json(text):
    try:
        obj=json.loads(text);a=obj.get("auth",obj)
        a={k:a[k] for k in ("uid","jid","kvToken","refreshToken","expireAt","region","resource") if k in a}
        for k in ("uid","jid","kvToken","resource"):
            if not isinstance(a.get(k),str) or not a[k]:raise ValueError()
        p=a["kvToken"].split(".")[1];claims=json.loads(base64.urlsafe_b64decode(p+"="*(-len(p)%4)))
        a["xmppJid"]=claims["xmpp_jid"]
        a["expireAt"]=int(claims["exp"])*1000
        domain=a["xmppJid"].split("/",1)[0].partition("@")[2]
        if not domain.endswith("-xmpp.my-alfred.com") or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789.-" for c in domain):raise ValueError()
        if "/" not in a["xmppJid"] or a["xmppJid"].split("/",1)[1]!=a["resource"]:raise ValueError()
        return a
    except (ValueError,TypeError,KeyError,IndexError,AttributeError):
        raise AuthError("Invalid session structure or routing") from None

class Client:
    def __init__(self,http,auth,save=None,auto_refresh=False):
        self.http=http;self.auth=dict(auth);self.save=save
        self.auto_refresh=auto_refresh;self.lock=asyncio.Lock()
    async def _ready(self):
        if self.auth["expireAt"]>(time.time()+300)*1000:return
        if not self.auto_refresh or not self.auth.get("refreshToken"):
            if self.auth["expireAt"]>(time.time()+30)*1000:return
            raise AuthError("Session expired; reauthenticate")
        async with self.http.post(API+"/v2.5/user/authbyRefreshToken",params={"jid":self.auth["jid"]},json={"refreshToken":self.auth["refreshToken"],"jid":self.auth["jid"]},allow_redirects=False) as r:
            if r.status in (401,403):raise AuthError("Refresh rejected")
            if r.status!=200:raise ProtocolError("Refresh HTTP failure")
            d=await r.json()
        if not d.get("kv_token") or not d.get("refreshToken"):raise AuthError("Unexpected refresh response")
        a=dict(self.auth,kvToken=d["kv_token"],refreshToken=d["refreshToken"])
        self.auth=session_from_json(json.dumps(a))
        if self.save:await self.save(self.auth)
    async def devices(self):
        async with self.lock:
            await self._ready()
            async with self.http.get(API+"/v2.5/device/camera",params={"ctype":3,"uid":self.auth["uid"]},headers={"Authorization":"Bearer "+self.auth["kvToken"]},allow_redirects=False) as r:
                if r.status in (401,403):raise AuthError("Camera list rejected")
                if r.status!=200:raise ProtocolError("Camera list HTTP failure")
                d=await r.json()
            if d.get("status") is not True or not isinstance(d.get("devices"),list):raise ProtocolError("Invalid camera list")
            return d["devices"]
    async def snapshot(self,device):
        async with self.lock:
            async with asyncio.timeout(45):
                await self._ready()
                return await self._snapshot(device)
    async def _snapshot(self,d):
        bare=self.auth["xmppJid"].split("/",1)[0];user,domain=bare.split("@",1)
        resource=d.get("jid","").partition("/")[2]
        owner=d.get("userId") or d.get("user_id")
        region=d.get("region") or self.auth.get("region")
        if not resource or not owner or not region:raise ProtocolError("Camera routing missing")
        target=f"{owner}@{region}-xmpp.my-alfred.com/{resource}"
        async with self.http.ws_connect(f"wss://{domain}/websocket",protocols=("xmpp",),origin="https://alfred.camera",max_msg_size=8000000) as ws:
            async def recv():
                e=await ws.receive(timeout=25)
                if e.type!=aiohttp.WSMsgType.TEXT:raise ProtocolError("XMPP connection closed")
                if "<!DOCTYPE" in e.data or "<!ENTITY" in e.data:raise ProtocolError("XML declaration rejected")
                try:n=ET.fromstring(e.data)
                except ET.ParseError:raise ProtocolError("Invalid XMPP XML") from None
                if n.tag==f"{{{S}}}failure":raise AuthError("XMPP authentication rejected")
                if n.tag=="{http://etherx.jabber.org/streams}error":raise ProtocolError("XMPP stream error; possible resource conflict")
                return n
            async def wait(predicate):
                while True:
                    n=await recv()
                    if predicate(n):return n
            opening=f'<open xmlns="{F}" to={quoteattr(domain)} version="1.0"/>'
            feat=lambda n:n.tag=="{http://etherx.jabber.org/streams}features"
            await ws.send_str(opening);n=await wait(feat)
            if "PLAIN" not in [x.text for x in n.iter(f"{{{S}}}mechanism")]:raise ProtocolError("SASL PLAIN unavailable")
            secret=base64.b64encode(("\0"+user+"\0"+self.auth["kvToken"]).encode()).decode()
            await ws.send_str(f'<auth xmlns="{S}" mechanism="PLAIN">{secret}</auth>')
            await wait(lambda n:n.tag==f"{{{S}}}success")
            await ws.send_str(opening);await wait(feat)
            await ws.send_str(f'<iq xmlns="{C}" type="set" id="bind-1"><bind xmlns="{B}"><resource>{escape(self.auth["resource"])}</resource></bind></iq>')
            n=await wait(lambda n:n.tag==f"{{{C}}}iq" and n.get("id")=="bind-1")
            if n.get("type")!="result":raise ProtocolError("Resource binding rejected")
            await ws.send_str(f'<presence xmlns="{C}"/>')
            encoded=base64.b64encode(request()).decode()
            await ws.send_str(f'<message xmlns="{C}" to={quoteattr(target)} id="rpc-1"><arpc ver="1" xmlns="alfred:pb">{encoded}</arpc></message>')
            while True:
                n=await recv()
                if n.tag==f"{{{C}}}iq" and n.get("type")=="get" and n.find("{urn:xmpp:ping}ping") is not None:
                    await ws.send_str(f'<iq xmlns="{C}" type="result" id={quoteattr(n.get("id",""))} to={quoteattr(n.get("from",""))}/>');continue
                if n.tag!=f"{{{C}}}message" or n.get("from")!=target:continue
                if n.get("type")=="error":raise ProtocolError("Camera returned routing error")
                rpc=n.find("{alfred:pb}arpc")
                if rpc is None or not rpc.text:continue
                try:m=fields(base64.b64decode("".join(rpc.text.split()),validate=True))
                except ValueError:raise ProtocolError("Invalid RPC encoding") from None
                if m.get(4)!=1 or m.get(1)!=1:continue
                if m.get(2)!=1 or m.get(3)!=2 or m.get(5,0):raise ProtocolError("Unexpected snapshot response")
                image=fields(m.get(6,b"")).get(1,b"")
                if not image.startswith(b"\xff\xd8") or not image.endswith(b"\xff\xd9"):raise ProtocolError("Invalid JPEG envelope")
                return image
