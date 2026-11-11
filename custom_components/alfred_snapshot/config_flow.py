import json
try:
    import probatio as vol
except ImportError:
    import voluptuous as vol
import aiohttp
from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .client import Client, session_from_json, AuthError, ProtocolError
from .const import DOMAIN

class AlfredFlow(config_entries.ConfigFlow, domain=DOMAIN):
    @staticmethod
    def async_get_options_flow(config_entry):
        from .options_flow import AlfredOptionsFlow
        return AlfredOptionsFlow()

    VERSION = 1
    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                auth = session_from_json(user_input["session_json"])
                client = Client(async_get_clientsession(self.hass), auth)
                devices = await client.devices()
                if not devices:
                    raise ProtocolError("No cameras")
            except AuthError:
                errors["base"] = "invalid_auth"
            except (aiohttp.ClientError, TimeoutError, ProtocolError):
                errors["base"] = "cannot_connect"
            else:
                old = self.context.get("entry_id")
                if old:
                    entry = self.hass.config_entries.async_get_entry(old)
                    if entry and entry.unique_id != auth["uid"]:
                        return self.async_abort(reason="wrong_account")
                    if entry:
                        self.hass.config_entries.async_update_entry(entry, data={**entry.data, "auth": auth})
                        await self.hass.config_entries.async_reload(entry.entry_id)
                        return self.async_abort(reason="reauth_successful")
                await self.async_set_unique_id(auth["uid"])
                self._abort_if_unique_id_configured()
                self._auth = auth
                self._devices = devices
                return await self.async_step_cameras()
        return self.async_show_form(step_id="user", data_schema=vol.Schema({vol.Required("session_json"): selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD))}), errors=errors)

    async def async_step_cameras(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="AlfredCamera Snapshots", data={"auth": self._auth, **user_input})
        choices = [selector.SelectOptionDict(value=d["_id"], label=d.get("label", d["_id"])) for d in self._devices if d.get("_id")]
        return self.async_show_form(step_id="cameras", data_schema=vol.Schema({
            vol.Required("cameras"): selector.SelectSelector(selector.SelectSelectorConfig(options=choices, multiple=True)),
            vol.Required("cache_seconds", default=60): vol.All(vol.Coerce(int), vol.Range(min=30,max=3600)),
            vol.Required("auto_refresh", default=False): bool,
        }))
    async def async_step_reauth(self, entry_data):
        return await self.async_step_user()
    async def async_step_reconfigure(self, user_input=None):
        return await self.async_step_user(user_input)
