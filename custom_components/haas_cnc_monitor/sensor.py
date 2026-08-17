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
    DID_POCKET,
    DID_POCKET_CAPACITY,
    DID_PROGRAM,
    DID_RAPID_OVERRIDE,
    DID_SPINDLE_OVERRIDE,
    DID_SPINDLE_SPEED,
    DID_SPINDLE_TIME,
    DID_THIS_CYCLE,
    DOMAIN,
    POCKET_EMPTY,
    POCKET_SPINDLE,
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
        suggested_display_precision=0,
        value_fn=lambda d: _num(d, DID_PART_COUNT),
    ),
    HaasSensorDescription(
        key="spindle_speed",
        name="Spindle speed",
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda d: _num(d, DID_SPINDLE_SPEED),
    ),
    HaasSensorDescription(
        key="spindle_override",
        name="Spindle override",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:percent-outline",
        suggested_display_precision=0,
        value_fn=lambda d: _num(d, DID_SPINDLE_OVERRIDE),
    ),
    HaasSensorDescription(
        key="feed_override",
        name="Feed override",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:percent-outline",
        suggested_display_precision=0,
        value_fn=lambda d: _num(d, DID_FEED_OVERRIDE),
    ),
    HaasSensorDescription(
        key="rapid_override",
        name="Rapid override",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:percent-outline",
        suggested_display_precision=0,
        value_fn=lambda d: _num(d, DID_RAPID_OVERRIDE),
    ),
    HaasSensorDescription(
        key="this_cycle",
        name="Current cycle time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        suggested_display_precision=1,
        value_fn=lambda d: _num(d, DID_THIS_CYCLE),
    ),
    HaasSensorDescription(
        key="cycle_remaining",
        name="Cycle remaining",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        suggested_display_precision=1,
        value_fn=lambda d: _num(d, DID_CYCLE_REMAINING),
    ),
    HaasSensorDescription(
        key="last_cycle",
        name="Last cycle time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _num(d, DID_LAST_CYCLE),
    ),
    HaasSensorDescription(
        key="machine_runtime",
        name="Machine runtime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        suggested_display_precision=1,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _num(d, DID_MACHINE_RUNTIME),
    ),
    HaasSensorDescription(
        key="spindle_time",
        name="Spindle time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        suggested_display_precision=1,
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
    entities: list[SensorEntity] = [
        HaasSensor(coordinator, entry, desc) for desc in SENSORS
    ]
    entities.append(HaasToolMagazineSensor(coordinator, entry))
    async_add_entities(entities)


def _parse_pockets(raw: str) -> tuple[int, bool]:
    """Return tools loaded in the magazine"""
    loaded = 0
    spindle = False
    for entry in raw.split(","):
        value = entry.strip()
        if value == POCKET_SPINDLE:
            spindle = True
        elif value and value != POCKET_EMPTY:
            loaded += 1
    return loaded, spindle


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


class HaasToolMagazineSensor(
    CoordinatorEntity[HaasMTConnectCoordinator], SensorEntity
):
    """Tool magazine load, e.g. "24/50" (or "24/50+1" counting the spindle)."""

    _attr_has_entity_name = True
    _attr_name = "Tool magazine"
    _attr_icon = "mdi:toolbox-outline"

    def __init__(
        self,
        coordinator: HaasMTConnectCoordinator,
        entry: HaasConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.unique_id}_tool_magazine"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
            name=entry.title,
            manufacturer="Haas Automation",
        )

    def _parts(self) -> tuple[int, int, bool] | None:
        """Return (loaded, capacity, spindle_present) or None if unavailable."""
        data = self.coordinator.data
        if not data:
            return None
        raw = data.values.get(DID_POCKET)
        cap = data.values.get(DID_POCKET_CAPACITY)
        if not raw or cap in (None, UNAVAILABLE):
            return None
        try:
            capacity = int(float(cap))
        except ValueError:
            return None
        loaded, spindle = _parse_pockets(raw)
        return loaded, capacity, spindle

    @property
    def native_value(self) -> str | None:
        parts = self._parts()
        if parts is None:
            return None
        loaded, capacity, spindle = parts
        total = loaded + (1 if spindle else 0)
        base = f"{total}/{capacity}"
        return f"{base}+1" if self.coordinator.count_spindle else base

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        parts = self._parts()
        if parts is None:
            return None
        loaded, capacity, spindle = parts
        return {
            "magazine_loaded": loaded + (1 if spindle else 0),
            "magazine_capacity": capacity,
            "spindle_tool_loaded": spindle,
            "count_spindle": self.coordinator.count_spindle,
        }
