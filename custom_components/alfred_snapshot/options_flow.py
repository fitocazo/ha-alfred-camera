"""Runtime options without exposing session credentials."""
import voluptuous as vol
from homeassistant import config_entries

class AlfredOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        entry = self.config_entry
        return self.async_show_form(step_id="init", data_schema=vol.Schema({
            vol.Required("cache_seconds", default=entry.options.get("cache_seconds", entry.data.get("cache_seconds", 60))): vol.All(vol.Coerce(int), vol.Range(min=30, max=3600)),
            vol.Required("auto_refresh", default=entry.options.get("auto_refresh", entry.data.get("auto_refresh", False))): bool,
        }))
