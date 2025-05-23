#  Copyright (C) 2022 Sam Steele
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import MedisafeApiClient
from .const import CONF_PASSWORD
from .const import CONF_USERNAME
from .const import DOMAIN

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


class MedisafeFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for medisafe."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        self._errors = {}

        if user_input is not None:
            valid = await self._test_credentials(
                user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
            )
            if valid:
                if (
                    self.source == config_entries.SOURCE_RECONFIGURE
                    or self.source == config_entries.SOURCE_REAUTH
                ):
                    return self.async_update_reload_and_abort(
                        self.hass.config_entries.async_get_entry(
                            self.context["entry_id"]
                        ),
                        data=user_input,
                    )
                else:
                    return self.async_create_entry(
                        title=user_input[CONF_USERNAME], data=user_input
                    )
            else:
                self._errors["base"] = "auth"

            return await self._show_config_form(user_input)

        return await self._show_config_form(user_input)

    async def async_step_reconfigure(self, user_input=None):
        self._errors = {}
        return await self._show_config_form(user_input)

    async def async_step_reauth(self, user_input=None):
        self._errors = {}
        return await self._show_config_form(user_input)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str}
            ),
            errors=self._errors,
        )

    async def _test_credentials(self, username, password):
        """Return true if credentials is valid."""
        try:
            client = MedisafeApiClient(
                username, password, async_create_clientsession(self.hass)
            )
            await client.async_get_data()
            return True
        except Exception:  # pylint: disable=broad-except
            pass
        return False
