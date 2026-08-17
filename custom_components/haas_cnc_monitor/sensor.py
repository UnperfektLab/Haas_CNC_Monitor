"""Sensor entities for Haas CNC Monitor."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    EntityCategory,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import HaasConfigEntry
from .const import (
    DID_CYCLE_REMAINING,
    DID_EXECUTION,
    DID_FEED_OVERRIDE,
    DID_LAST_CYCLE,
    DID_MACHINE_RUNTIME,
    DID_MODE,
    DID_PART_COUNT,
    DID_PROGRAM,
    DID_RAPID_OVERRIDE,
    DID_SPINDLE_OVERRIDE,
    DID_SPINDLE_SPEED,
    DID_SPINDLE_TIME,
    DID_THIS_CYCLE,
    DOMAIN,
    UNAVAILABLE,
)
from .coordinator import HaasMTConnectCoordinator
from .mtconnect import MTConnectData


@dataclass(frozen=True, kw_only=True)
class HaasSensorDescription(SensorEntityDescription):
    """Describes a Haas sensor and how to pull it from a snapshot."""

    value_fn: Callable[[MTConnectData], str | float | None]


def _num(data: MTConnectData, did: str) -> float | None:
    raw = data.values.get(did)
    if raw is None or raw == UNAVAILABLE:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _text(data: MTConnectData, did: str) -> str | None:
    raw = data.values.get(did)
    return None if raw in (None, UNAVAILABLE) else raw


SENSORS: tuple[HaasSensorDescription, ...] = (
    HaasSensorDescription(
        key="execution",
        name="Execution",
        icon="mdi:play-circle-outline",
        device_class=SensorDeviceClass.ENUM,
        options=[
            "ACTIVE",
            "READY",
            "STOPPED",
            "INTERRUPTED",
            "FEED_HOLD",
            "OPTIONAL_STOP",
            "PROGRAM_STOPPED",
        ],
        value_fn=lambda d: _text(d, DID_EXECUTION),
    ),
    HaasSensorDescription(
        key="controller_mode",
        name="Controller mode",
        icon="mdi:cog-outline",
        value_fn=lambda d: _text(d, DID_MODE),
    ),
    HaasSensorDescription(
        key="program",
        name="Program",
        icon="mdi:file-code-outline",
        value_fn=lambda d: _text(d, DID_PROGRAM),
    ),
    HaasSensorDescription(
        key="part_count",
        name="Part count",
        icon="mdi:counter",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: _num(d, DID_PART_COUNT),
    ),
    HaasSensorDescription(
        key="spindle_speed",
        name="Spindle speed",
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _num(d, DID_SPINDLE_SPEED),
    ),
    HaasSensorDescription(
        key="spindle_override",
        name="Spindle override",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:percent-outline",
        value_fn=lambda d: _num(d, DID_SPINDLE_OVERRIDE),
    ),
    HaasSensorDescription(
        key="feed_override",
        name="Feed override",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:percent-outline",
        value_fn=lambda d: _num(d, DID_FEED_OVERRIDE),
    ),
    HaasSensorDescription(
        key="rapid_override",
        name="Rapid override",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:percent-outline",
        value_fn=lambda d: _num(d, DID_RAPID_OVERRIDE),
    ),
    HaasSensorDescription(
        key="this_cycle",
        name="Current cycle time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=lambda d: _num(d, DID_THIS_CYCLE),
    ),
    HaasSensorDescription(
        key="cycle_remaining",
        name="Cycle remaining",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=lambda d: _num(d, DID_CYCLE_REMAINING),
    ),
    HaasSensorDescription(
        key="last_cycle",
        name="Last cycle time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _num(d, DID_LAST_CYCLE),
    ),
    HaasSensorDescription(
        key="machine_runtime",
        name="Machine runtime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _num(d, DID_MACHINE_RUNTIME),
    ),
    HaasSensorDescription(
        key="spindle_time",
        name="Spindle time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _num(d, DID_SPINDLE_TIME),
    ),
    HaasSensorDescription(
        key="active_alarm",
        name="Active alarm",
        icon="mdi:alert-circle-outline",
        value_fn=lambda d: "; ".join(d.alarms) if d.alarms else "OK",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HaasConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator = entry.runtime_data
    async_add_entities(HaasSensor(coordinator, entry, desc) for desc in SENSORS)


class HaasSensor(CoordinatorEntity[HaasMTConnectCoordinator], SensorEntity):
    """A single Haas CNC Monitor sensor."""

    _attr_has_entity_name = True
    entity_description: HaasSensorDescription

    def __init__(
        self,
        coordinator: HaasMTConnectCoordinator,
        entry: HaasConfigEntry,
        description: HaasSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
            name=entry.title,
            manufacturer="Haas Automation",
            model=coordinator.data.device_name if coordinator.data else None,
        )

    @property
    def native_value(self) -> str | float | None:
        return self.entity_description.value_fn(self.coordinator.data)
