"""Rasterize the Alfred WebViewer symbol to HA brand PNGs using only stdlib."""
from pathlib import Path
import math
import re
import struct
import xml.etree.ElementTree as ET
import zlib

ROOT = Path(__file__).resolve().parents[1]

def polygons():
    svg = ET.parse(ROOT / "assets/alfred-symbol.svg").getroot()
    result = []
    for path in svg.findall("{http://www.w3.org/2000/svg}path"):
        tokens = re.findall(r"[MLHVZ]|-?\d+(?:\.\d+)?", path.attrib["d"])
        points = []; i = 0; x = y = 0
        while i < len(tokens):
            op = tokens[i]; i += 1
            if op in ("M", "L"):
                x = float(tokens[i]); y = float(tokens[i+1]); i += 2
            elif op == "H": x = float(tokens[i]); i += 1
            elif op == "V": y = float(tokens[i]); i += 1
            elif op == "Z": continue
            else: raise ValueError("Unsupported SVG command")
            points.append((x, y))
        color = bytes.fromhex(path.attrib["fill"].lstrip("#")) + b"\xff"
        result.append((points, color))
    return result

def render(size, shapes):
    coords = [p for points, _ in shapes for p in points]
    minx = min(p[0] for p in coords); maxx = max(p[0] for p in coords)
    miny = min(p[1] for p in coords); maxy = max(p[1] for p in coords)
    span = max(maxx-minx, maxy-miny)
    scale = size/span
    ox = (size-(maxx-minx)*scale)/2-minx*scale
    oy = (size-(maxy-miny)*scale)/2-miny*scale
    rows = [bytearray(size*4) for _ in range(size)]
    for points, color in shapes:
        points = [(x*scale+ox, y*scale+oy) for x,y in points]
        edges = list(zip(points, points[1:]+points[:1]))
        for y, row in enumerate(rows):
            py = y+.5
            hits = sorted(x1+(py-y1)*(x2-x1)/(y2-y1) for (x1,y1),(x2,y2) in edges if (y1<=py<y2) or (y2<=py<y1))
            for i in range(0,len(hits),2):
                lo = max(0,math.ceil(hits[i]-.5)); hi = min(size,math.ceil(hits[i+1]-.5))
                if hi>lo: row[lo*4:hi*4] = color*(hi-lo)
    def chunk(kind, data):
        return struct.pack(">I",len(data))+kind+data+struct.pack(">I",zlib.crc32(kind+data)&0xffffffff)
    raw = b"".join(b"\0"+bytes(row) for row in rows)
    return b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",size,size,8,6,0,0,0))+chunk(b"IDAT",zlib.compress(raw,9))+chunk(b"IEND",b"")

if __name__ == "__main__":
    dest = ROOT / "custom_components/alfred_snapshot/brand"
    dest.mkdir(parents=True, exist_ok=True)
    shapes = polygons()
    for size,name in [(256,"icon.png"),(512,"icon@2x.png")]:
        image = render(size, shapes)
        (dest/name).write_bytes(image)
        print(f"Generated {name}: {size}x{size}, {len(image)} bytes")
