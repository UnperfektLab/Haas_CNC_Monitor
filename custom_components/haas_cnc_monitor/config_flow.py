"""Config flow for Haas CNC Monitor."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_ADVANCED,
    CONF_COUNT_SPINDLE,
    CONF_HOST,
    CONF_PORT,
    DEFAULT_COUNT_SPINDLE,
    DEFAULT_PORT,
    DOMAIN,
)
from .mtconnect import MTConnectClient, MTConnectError


class HaasMTConnectConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Haas CNC Monitor."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return HaasOptionsFlow()

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
                # Flatten the collapsible "advanced" section into the entry data.
                advanced = user_input.get(CONF_ADVANCED, {})
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                        CONF_COUNT_SPINDLE: advanced.get(
                            CONF_COUNT_SPINDLE, DEFAULT_COUNT_SPINDLE
                        ),
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_ADVANCED): section(
                    vol.Schema(
                        {
                            vol.Required(
                                CONF_COUNT_SPINDLE, default=DEFAULT_COUNT_SPINDLE
                            ): bool,
                        }
                    ),
                    {"collapsed": True},
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class HaasOptionsFlow(OptionsFlow):
    """Allow changing the spindle-counting option after setup."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        # Current value: option override, else the value chosen at setup.
        current = self.config_entry.options.get(
            CONF_COUNT_SPINDLE,
            self.config_entry.data.get(CONF_COUNT_SPINDLE, DEFAULT_COUNT_SPINDLE),
        )
        schema = vol.Schema(
            {vol.Required(CONF_COUNT_SPINDLE, default=current): bool}
        )
        return self.async_show_form(step_id="init", data_schema=schema)
