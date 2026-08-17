"""Config flow for Haas CNC Monitor."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_HOST, CONF_PORT, DEFAULT_PORT, DOMAIN
from .mtconnect import MTConnectClient, MTConnectError


class HaasMTConnectConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Haas CNC Monitor."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            client = MTConnectClient(
                async_get_clientsession(self.hass),
                user_input[CONF_HOST],
                user_input[CONF_PORT],
            )
            try:
                data = await client.async_probe()
            except MTConnectError:
                errors["base"] = "cannot_connect"
            else:
                # NGC machines all report uuid="000", so we key on the host.
                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()
                title = data.device_name or f"Haas {user_input[CONF_HOST]}"
                return self.async_create_entry(title=title, data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
