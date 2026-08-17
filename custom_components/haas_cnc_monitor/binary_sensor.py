"""Binary sensors for Haas CNC Monitor: connectivity, running, and problem."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import HaasConfigEntry
from .const import (
    CONDITION_STATES_FAULT,
    DID_ESTOP,
    DID_EXECUTION,
    DID_MACHINE_CONDITION,
    DOMAIN,
)
from .coordinator import HaasMTConnectCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HaasConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            HaasAvailability(coordinator, entry),
            HaasRunning(coordinator, entry),
            HaasProblem(coordinator, entry),
        ]
    )


class _HaasBinaryBase(CoordinatorEntity[HaasMTConnectCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HaasMTConnectCoordinator,
        entry: HaasConfigEntry,
        key: str,
        name: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.unique_id}_{key}"
        self._attr_name = name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
            name=entry.title,
            manufacturer="Haas Automation",
        )


class HaasAvailability(_HaasBinaryBase):
    """Whether the agent is reachable."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "availability", "Availability")

    @property
    def available(self) -> bool:
        # Keep this entity itself always available so it can report "off".
        return True

    @property
    def is_on(self) -> bool:
        return self.coordinator.last_update_success


class HaasRunning(_HaasBinaryBase):
    """On when the program is actively executing (Execution == ACTIVE)."""

    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "running", "Running")

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data
        if not data:
            return None
        return data.values.get(DID_EXECUTION) == "ACTIVE"


class HaasProblem(_HaasBinaryBase):
    """On when E-stop is pressed, the machine Condition is Fault/Warning, or
    there is an active alarm."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "problem", "Problem")

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data
        if not data:
            return None
        # EmergencyStop is TRIGGERED when pressed, ARMED when released/ok.
        if data.values.get(DID_ESTOP) == "TRIGGERED":
            return True
        if data.conditions.get(DID_MACHINE_CONDITION) in CONDITION_STATES_FAULT:
            return True
        return bool(data.alarms)

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        data = self.coordinator.data
        if not data:
            return {}
        return {
            "estop": data.values.get(DID_ESTOP),
            "machine_condition": data.conditions.get(DID_MACHINE_CONDITION),
            "active_alarms": data.alarms,
        }
