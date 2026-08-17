"""Constants for the Haas CNC Monitor integration."""

from __future__ import annotations

DOMAIN = "haas_cnc_monitor"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_ADVANCED = "advanced"
CONF_COUNT_SPINDLE = "count_spindle"  # add the spindle as an extra "+1" slot

DEFAULT_PORT = 8082
DEFAULT_SCAN_INTERVAL = 10  # seconds
DEFAULT_COUNT_SPINDLE = True

# MTConnect uses this sentinel when a DataItem has no valid reading.
UNAVAILABLE = "UNAVAILABLE"

# --- Canonical DataItem IDs on Haas NGC (verified against real data) ---
DID_EXECUTION = "rstat"          # Execution: ACTIVE / STOPPED / ...
DID_MODE = "mode"                # ControllerMode: AUTOMATIC / MANUAL / ...
DID_PROGRAM = "ncprog"           # running NC program name
DID_ESTOP = "estop"              # EmergencyStop: ARMED (ok) / TRIGGERED (pressed)
DID_PART_COUNT = "m30c1"         # M30 counter #1 (parts completed)
DID_PART_COUNT_2 = "m30c2"       # M30 counter #2
DID_SPINDLE_SPEED = "sspeed"     # actual spindle RPM
DID_SPINDLE_OVERRIDE = "ssovrd"  # spindle override %
DID_FEED_OVERRIDE = "fdovrd"     # feedrate override %
DID_RAPID_OVERRIDE = "rovrd"     # rapid override %
DID_THIS_CYCLE = "tcycle"        # current cycle elapsed (s)
DID_LAST_CYCLE = "lcycle"        # previous cycle duration (s)
DID_CYCLE_REMAINING = "cyremtim"  # estimated remaining (s)
DID_MACHINE_RUNTIME = "machineruntime"  # cumulative powered time
DID_SPINDLE_TIME = "spindletime"        # cumulative spindle-on time
DID_LOOPS_REMAINING = "lpremain"

# Tool magazine. `pockets` (name STATION) is the magazine size. `pocket` is a
# CSV where each entry is a tool's physical pocket: -101 = empty, 0 = spindle.
DID_POCKET = "pocket"
DID_POCKET_CAPACITY = "pockets"
POCKET_EMPTY = "-101"
POCKET_SPINDLE = "0"

# The single overall machine Condition (SYSTEM category).
DID_MACHINE_CONDITION = "mcond"
# The Haas-specific active-alarms container.
DID_ACTIVE_ALARMS = "aalarms"

CONDITION_STATES = ("Normal", "Warning", "Fault", "Unavailable")
CONDITION_STATES_FAULT = {"Fault", "Warning"}
