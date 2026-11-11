import asyncio
from datetime import datetime, timezone
import time
import aiohttp
from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.helpers.device_registry import DeviceInfo
from .client import AuthError, ProtocolError
from .const import DOMAIN
from .selection import selected_cameras

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    selected = set(selected_cameras(entry))
    async_add_entities([AlfredCamera(entry, data["client"], d) for d in data["devices"] if d.get("_id") in selected])

class AlfredCamera(Camera):
    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_name = None
    _attr_brand = "AlfredCamera"
    _attr_supported_features = CameraEntityFeature(0)
    def __init__(self, entry, client, device):
        super().__init__()
        self._entry = entry
        self._client = client
        self._device = device
        self._attr_unique_id = f"{entry.unique_id}_{device['_id']}"
        self._attr_model = device.get("device", "Camera")
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, self._attr_unique_id)}, name=device.get("label", "AlfredCamera"), manufacturer=device.get("vendor", "AlfredCamera"), model=self._attr_model)
        self._image = None
        self._last = 0
        self._retry = 0
        self._success = None
        self._error = None
        self._lock = asyncio.Lock()
        self._ttl = entry.options.get("cache_seconds", entry.data.get("cache_seconds", 60))
    @property
    def frame_interval(self):
        return float(self._ttl)
    @property
    def extra_state_attributes(self):
        return {"last_snapshot_success": self._success, "snapshot_error": self._error, "snapshot_cache_seconds": self._ttl}
    async def async_camera_image(self, width=None, height=None):
        return await self._async_fetch_image(force=False)

    async def async_force_snapshot(self):
        image = await self._async_fetch_image(force=True)
        if image is None:
            from homeassistant.exceptions import HomeAssistantError
            raise HomeAssistantError("Falha ao obter novo snapshot Alfred; consulte snapshot_error")

    async def _async_fetch_image(self, force=False):
        async with self._lock:
            now = time.monotonic()
            if not force and self._image is not None and now-self._last < self._ttl:
                return self._image
            if not force and now < self._retry:
                return None
            try:
                image = await self._client.snapshot(self._device)
            except AuthError:
                self._error = "authentication"
                self._retry = time.monotonic()+self._ttl
                self._entry.async_start_reauth(self.hass)
                self.async_write_ha_state()
                return None
            except (TimeoutError, aiohttp.ClientError, ProtocolError):
                self._error = "connection_or_protocol"
                self._retry = time.monotonic()+self._ttl
                self.async_write_ha_state()
                return None
            self._image = image
            self._last = time.monotonic()
            self._success = datetime.now(timezone.utc).isoformat()
            self._error = None
            self.async_write_ha_state()
            return image
