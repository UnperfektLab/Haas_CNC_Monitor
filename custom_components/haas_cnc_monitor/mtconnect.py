"""Minimal async MTConnect client + parser for Haas NGC agents.

The Haas NGC control embeds an MTConnect agent on (by default) port 8082 and
serves XML over HTTP:

"""

from __future__ import annotations

from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

import aiohttp

from .const import CONDITION_STATES, DID_ACTIVE_ALARMS


class MTConnectError(Exception):
    """Raised when the agent cannot be reached or returns invalid data."""


def _local(tag: str) -> str:
    """Strip the '{namespace}' prefix from an ElementTree tag."""
    return tag.rsplit("}", 1)[-1]


@dataclass
class MTConnectData:
    """A flattened snapshot of the /current response.

    ``values`` maps dataItemId -> latest string value.
    ``conditions`` maps dataItemId -> condition state (Normal/Warning/Fault/...).
    ``alarms`` is the list of active alarm strings (empty if none).
    """

    device_name: str | None = None
    values: dict[str, str] = field(default_factory=dict)
    conditions: dict[str, str] = field(default_factory=dict)
    alarms: list[str] = field(default_factory=list)


class MTConnectClient:
    """Fetches and parses the MTConnect /current document."""

    def __init__(self, session: aiohttp.ClientSession, host: str, port: int) -> None:
        self._session = session
        self._base = f"http://{host}:{port}"

    async def _get(self, path: str) -> str:
        url = f"{self._base}/{path}"
        try:
            async with self._session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                resp.raise_for_status()
                return await resp.text()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise MTConnectError(f"Cannot reach agent at {url}: {err}") from err

    async def async_probe(self) -> MTConnectData:
        """Verify connectivity and read device identity (used by config flow)."""
        return self._parse(await self._get("current"))

    async def async_current(self) -> MTConnectData:
        """Poll the latest values."""
        return self._parse(await self._get("current"))

    @staticmethod
    def _parse(xml: str) -> MTConnectData:
        try:
            root = ET.fromstring(xml)
        except ET.ParseError as err:
            raise MTConnectError(f"Invalid MTConnect XML: {err}") from err

        data = MTConnectData()

        for elem in root.iter():
            tag = _local(elem.tag)

            if tag == "DeviceStream":
                data.device_name = elem.get("name") or data.device_name
                continue

            if tag in CONDITION_STATES:
                did = elem.get("dataItemId")
                if did:
                    data.conditions[did] = tag
                continue

            if tag == "Alarm":
                text = (elem.text or "").strip()
                if text:
                    data.alarms.append(text)
                continue

            did = elem.get("dataItemId")
            if not did:
                continue
            # Skip the alarm container itself unless it carries plain text
            # (the nested <Alarm> children are handled above).
            text = (elem.text or "").strip()
            if did == DID_ACTIVE_ALARMS:
                if text and text.upper() != "NO ACTIVE ALARMS":
                    data.alarms.append(text)
                continue
            if text:
                data.values[did] = text

        return data
