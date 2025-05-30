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
import asyncio
import logging
import socket
from datetime import datetime
from datetime import timedelta

import aiohttp
import async_timeout
from homeassistant.exceptions import ConfigEntryAuthFailed

TIMEOUT = 120

_LOGGER: logging.Logger = logging.getLogger(__package__)


class MedisafeApiClient:
    def __init__(
        self, username: str, password: str, session: aiohttp.ClientSession
    ) -> None:
        self._username = username
        self._password = password
        self._session = session

    async def async_get_data(self) -> dict:
        auth = await self.api_wrapper(
            "post",
            "https://api.medisafeproject.com/api/v3/auth/login",
            {"account": self._username, "password": self._password},
        )
        if "error" in auth:
            print(auth)
            if "message" in auth["error"]:
                _LOGGER.error(f"Authentication failed: {auth['error']['message']}")
                raise ConfigEntryAuthFailed(auth["error"]["message"])
            else:
                _LOGGER.error(f"Authentication failed: {auth['error']}")
                raise ConfigEntryAuthFailed(auth["error"])

        if "token" not in auth:
            _LOGGER.error("No token recieved")
            raise ConfigEntryAuthFailed("Authentication Failed")

        start = int((datetime.today() - timedelta(days=1)).timestamp() * 1000)
        end = int((datetime.today() + timedelta(days=1)).timestamp() * 1000)
        return await self.api_wrapper(
            "get",
            f"https://api.medisafeproject.com/api/v3/user/{auth['user']['id']}/sync?from=0&fromUpdate=0&includeDeleted=true&includeItems=true&includeClient=true&sync=true&send_pages_sev=false",
            headers={"Authorization": "Bearer " + auth["token"]['accessToken'], "X-Operation-Execution-Timestamp": str(start)},
        )

    async def api_wrapper(
        self, method: str, url: str, data: dict = None, headers: dict = None
    ) -> dict:
        try:
            async with async_timeout.timeout(TIMEOUT):
                if method == "get":
                    response = await self._session.get(url, headers=headers)
                    return await response.json()

                elif method == "post":
                    response = await self._session.post(url, headers=headers, json=data)
                    return await response.json()

        except asyncio.TimeoutError as exception:
            _LOGGER.error(
                "Timeout error fetching information from %s - %s", url, exception
            )

        except (KeyError, TypeError) as exception:
            _LOGGER.error("Error parsing information from %s - %s", url, exception)
        except (aiohttp.ClientError, socket.gaierror) as exception:
            _LOGGER.error("Error fetching information from %s - %s", url, exception)
        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error("Something really wrong happened! - %s", exception)
