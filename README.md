# Haas CNC Monitor — Home Assistant integration

> Unofficial project, not affiliated with Haas Automation, Inc. "Haas" is used
> descriptively (compatibility only).

A Home Assistant custom integration that polls the MTConnect agent built into
Haas **NGC** controls and exposes a curated set of entities — run state, alarms,
production and key parameters — instead of every single DataItem.

## Install via HACS (recommended)

This is a custom repository. Click the button to open your Home Assistant and
add it to HACS, then press **Download**:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=UnperfektLab&repository=Haas_CNC_Monitor&category=integration)

After downloading, **restart Home Assistant**, then go to
**Settings → Devices & services → Add integration → Haas CNC Monitor** and enter
the machine IP.

<details>
<summary>Manual install (without HACS)</summary>

Copy the folder `custom_components/haas_cnc_monitor/` into your HA config
(`<config>/custom_components/haas_cnc_monitor/`), restart Home Assistant, then
add the integration as above.
</details>

> Add each machine separately (by its IP).

## Machine-side setup (NGC)

1. Network: connect the machine to the local network; a static IP for the machine is recommended.
2. Firewall: agent port **8082/TCP** must not be blocked.
3. Control software `100.20.000.1200` or newer.

Quick check in a browser: `http://<ip>:8082/current` should return XML.

## Entities (mapped to real `dataItemId`)

| Entity | dataItemId | Notes |
|---|---|---|
| `binary_sensor` Availability | — | from poll success (NGC does not emit `Availability`) |
| `binary_sensor` Running | `rstat` | on when `Execution == ACTIVE` |
| `binary_sensor` Problem | `estop` + `mcond` + alarms | on when E-stop `TRIGGERED`, Condition `Fault/Warning`, or an active alarm |
| `sensor` Execution | `rstat` | ACTIVE / STOPPED / … |
| `sensor` Controller mode | `mode` | AUTOMATIC / MANUAL / MDI / … |
| `sensor` Program | `ncprog` | running NC program name |
| `sensor` Part count | `m30c1` | M30 counter #1 (total_increasing) |
| `sensor` Spindle speed | `sspeed` | RPM (actual) |
| `sensor` Spindle override | `ssovrd` | % |
| `sensor` Feed override | `fdovrd` | % |
| `sensor` Rapid override | `rovrd` | % |
| `sensor` Current cycle time | `tcycle` | s |
| `sensor` Cycle remaining | `cyremtim` | s (estimated) |
| `sensor` Last cycle time | `lcycle` | s (diagnostic) |
| `sensor` Machine runtime | `machineruntime` | cumulative counter (diagnostic) |
| `sensor` Spindle time | `spindletime` | cumulative counter (diagnostic) |
| `sensor` Active alarm | `aalarms` | alarm text or `OK` |

## Example automations

```yaml
# Push when an alarm / E-stop occurs
- alias: Haas VF5 - alarm
  trigger:
    - platform: state
      entity_id: binary_sensor.vf_5ss_problem
      to: "on"
  action:
    - service: notify.mobile_app
      data:
        title: "Haas VF-5SS - ALARM"
        message: "{{ state_attr('binary_sensor.vf_5ss_problem','active_alarms') | join(', ') }}"

# Notify on a completed part (M30 counter increment)
- alias: Haas VF5 - part done
  trigger:
    - platform: state
      entity_id: sensor.vf_5ss_part_count
  condition:
    - "{{ trigger.to_state.state | int(0) > trigger.from_state.state | int(0) }}"
  action:
    - service: notify.mobile_app
      data:
        message: "Part number {{ trigger.to_state.state }} finished"

# Machine idle too long while in AUTO
- alias: Haas VF5 - idle
  trigger:
    - platform: state
      entity_id: binary_sensor.vf_5ss_running
      to: "off"
      for: "00:15:00"
  condition:
    - "{{ states('sensor.vf_5ss_controller_mode') == 'AUTOMATIC' }}"
  action:
    - service: notify.mobile_app
      data:
        message: "VF-5SS idle >15 min in AUTO mode"
```

## License

[MIT](LICENSE) © 2026 UnperfektLab
