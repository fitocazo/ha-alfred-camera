"""Register Alfred camera actions."""
from homeassistant.core import callback
from homeassistant.helpers import service
from .const import DOMAIN

@callback
def async_setup_services(hass):
    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        "refresh_snapshot",
        entity_domain="camera",
        schema={},
        func="async_force_snapshot",
    )
