from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import aiohttp
from .const import DOMAIN, PLATFORMS
from .client import Client, AuthError, ProtocolError


async def async_setup(hass, config):
    from .services import async_setup_services
    async_setup_services(hass)
    return True

async def async_setup_entry(hass, entry):
    if not hass.services.has_service(DOMAIN, "refresh_snapshot"):
        from .services import async_setup_services
        async_setup_services(hass)
    async def save(auth):
        hass.config_entries.async_update_entry(entry, data={**entry.data, "auth": auth})
    client = Client(async_get_clientsession(hass), entry.data["auth"], save, entry.options.get("auto_refresh", entry.data.get("auto_refresh", False)))
    try:
        devices = await client.devices()
    except AuthError as err:
        raise ConfigEntryAuthFailed("Sessao Alfred invalida; importe uma sessao nova") from None
    except (aiohttp.ClientError, TimeoutError, ProtocolError):
        raise ConfigEntryNotReady("Falha ao consultar Alfred") from None
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"client": client, "devices": devices}
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass, entry):
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)
        return True
    return False

async def _async_options_updated(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)
