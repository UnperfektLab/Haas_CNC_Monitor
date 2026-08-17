"""DataUpdateCoordinator for Haas CNC Monitor."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_COUNT_SPINDLE,
    CONF_HOST,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DEFAULT_COUNT_SPINDLE,
    DEFAULT_SCAN_INTERVAL,
)
from .mtconnect import MTConnectClient, MTConnectData, MTConnectError

_LOGGER = logging.getLogger(__name__)


class HaasMTConnectCoordinator(DataUpdateCoordinator[MTConnectData]):
    """Polls the machine's /current endpoint on a fixed interval."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name="Haas CNC Monitor",
            update_interval=timedelta(seconds=interval),
        )
        self.client = MTConnectClient(
            async_get_clientsession(hass),
            entry.data[CONF_HOST],
            entry.data[CONF_PORT],
        )
        self.count_spindle: bool = entry.options.get(
            CONF_COUNT_SPINDLE,
            entry.data.get(CONF_COUNT_SPINDLE, DEFAULT_COUNT_SPINDLE),
        )

    async def _async_update_data(self) -> MTConnectData:
        try:
            return await self.client.async_current()
        except MTConnectError as err:
            raise UpdateFailed(str(err)) from err
