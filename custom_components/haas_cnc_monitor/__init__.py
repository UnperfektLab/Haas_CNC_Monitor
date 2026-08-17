"""The Haas CNC Monitor integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import HaasMTConnectCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

type HaasConfigEntry = ConfigEntry[HaasMTConnectCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: HaasConfigEntry) -> bool:
    """Set up Haas CNC Monitor from a config entry."""
    coordinator = HaasMTConnectCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # Reload when options (e.g. count_spindle) change so the new value applies.
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HaasConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(hass: HomeAssistant, entry: HaasConfigEntry) -> None:
    """Reload the entry after the options flow updates settings."""
    await hass.config_entries.async_reload(entry.entry_id)
