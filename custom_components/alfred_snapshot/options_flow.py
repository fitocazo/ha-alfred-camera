"""Runtime camera and snapshot options without exposing credentials."""
import asyncio
import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .client import Client, AuthError, ProtocolError
from .selection import camera_options, selected_cameras


class AlfredOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        entry = self.config_entry
        selected = selected_cameras(entry)
        errors = {}
        if not hasattr(self, "_camera_options"):
            try:
                client = Client(async_get_clientsession(self.hass), entry.data["auth"])
                async with asyncio.timeout(20):
                    devices = await client.devices()
            except AuthError:
                errors["base"] = "invalid_auth"
            except (aiohttp.ClientError, TimeoutError, ProtocolError):
                errors["base"] = "cannot_connect"
            else:
                self._camera_options = camera_options(devices, selected)

        choices = getattr(self, "_camera_options", camera_options([], selected))
        if user_input is not None and not errors:
            cameras = user_input.get("cameras", [])
            allowed = {choice["value"] for choice in choices}
            if not cameras:
                errors["cameras"] = "no_cameras"
            elif any(camera_id not in allowed for camera_id in cameras):
                errors["cameras"] = "invalid_camera"
            else:
                return self.async_create_entry(title="", data={**entry.options, **user_input})

        defaults = {**entry.options, **(user_input or {})}
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("cameras", default=defaults.get("cameras", selected)): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=choices, multiple=True)
                ),
                vol.Required("cache_seconds", default=defaults.get("cache_seconds", entry.data.get("cache_seconds", 60))): vol.All(vol.Coerce(int), vol.Range(min=30, max=3600)),
                vol.Required("auto_refresh", default=defaults.get("auto_refresh", entry.data.get("auto_refresh", False))): bool,
            }),
            errors=errors,
        )
