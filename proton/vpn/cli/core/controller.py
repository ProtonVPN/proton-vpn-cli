"""
Core CLI logic.

Copyright (c) 2025 Proton AG

This file is part of Proton VPN.

Proton VPN is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Proton VPN is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ProtonVPN.  If not, see <https://www.gnu.org/licenses/>.
"""
import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from importlib import metadata
import logging
import random
from types import TracebackType
from typing import Callable, List, Optional, Type, Union

from click.core import Context as ClickContext
from packaging.version import Version
import sentry_sdk

from proton.session.exceptions import ProtonAPIAuthenticationNeeded
from proton.vpn.core.settings.custom_dns import CustomDNSEntry, CustomDNS
from proton.vpn import logging as ProtonLogging
from proton.vpn.cli.core.exception_handler import ExceptionHandler
from proton.vpn.cli.core.exceptions import \
    Authentication2FAFailedError, \
    AuthenticationRequiredError, \
    AuthenticationFailedError, \
    CountryCodeError, \
    CountryNameError, \
    InvalidDNS, \
    RequiresHigherTierError, \
    SignoutRequiredError, \
    VPNConnectionError
from proton.vpn.connection import states
from proton.vpn.connection.enum import ConnectionStateEnum
from proton.vpn.core.api import ProtonVPNAPI
from proton.vpn.core.connection import VPNStateSubscriber, VPNConnection, VPNConnector
from proton.vpn.core.session_holder import ClientTypeMetadata
from proton.vpn.core.settings import Settings
from proton.vpn.session import ServerList
from proton.vpn.session.dataclasses.servers import Country
from proton.vpn.session.servers.country_codes import \
    validate_country_code, \
    get_country_code_for_name
from proton.vpn.session.servers.types import LogicalServer, ServerFeatureEnum

LOGGING_FILENAME = "vpn-cli"
DEFAULT_CLI_NAME = "protonvpn"


@dataclass
class Feature:
    """Used when setting and saving features."""
    setting_path: str = None
    available_on_free_tier: bool = False
    requires_restart: bool = False


@dataclass
class Params:
    """The parameters for constructing the Controller"""
    verbose: str = False
    allow_gui_concurrency: bool = False
    overriding_controller: Optional['Controller'] = None


@asynccontextmanager
async def _wait_for_event(  # pylint: disable=R0913
    connector: VPNConnector,
    event_types: Optional[List[ConnectionStateEnum]] = None,
    timeout=10
):
    if not event_types:
        yield
        return

    event = asyncio.Event()

    class Subscriber(VPNStateSubscriber):  # pylint: disable=R0903
        """
        This class listens for a given set of status changes and then
        triggers the given event.
        """
        event_hit_count: int
        error_event_occurred: bool = False

        def status_update(self, status):
            if status.type in event_types:
                event.set()
            elif status.type is ConnectionStateEnum.ERROR:
                self.error_event_occurred = True
                event.set()

    subscriber = Subscriber()
    connector.register(subscriber)

    yield

    try:
        await asyncio.wait_for(event.wait(), timeout)

    except asyncio.exceptions.TimeoutError as exc:
        connector.unregister(subscriber)
        expected_types = ", ".join(ConnectionStateEnum(type).name for type in event_types)  # noqa: E501 # pylint: disable=C0301
        logger = ProtonLogging.getLogger(__name__)
        logger.error(f"Timed out after {timeout}s waiting for event(s): {expected_types}")
        raise TimeoutError from exc

    connector.unregister(subscriber)
    if subscriber.error_event_occurred:
        raise VPNConnectionError


class Controller:  # pylint: disable=too-many-public-methods
    """
    The application business logic is in this class. The is the core of the
    application.
    """
    def __init__(
        self,
        params: Params,
        click_ctx: ClickContext,
        api: ProtonVPNAPI = None
    ):
        ProtonLogging.config(filename=LOGGING_FILENAME)
        logger = logging.getLogger()  # grab the root logger
        if params.verbose:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.ERROR)

        client_type_metadata = ClientTypeMetadata(
            type="cli"
        )

        ExceptionHandler.enable(exception_reporter=self)
        self._api = api or ProtonVPNAPI(client_type_metadata)
        self._click_context = click_ctx

    @staticmethod
    async def create(params: Params, click_ctx: ClickContext):
        """Preferred method to get an instance of Controller."""
        controller = params.overriding_controller or Controller(params, click_ctx)
        # Ensure controller always has settings loaded,
        # even if only using free user defaults prior to authentication.
        # This allows crash reporting to work prior to sign in.
        await controller.get_settings()
        return controller

    def set_uncaught_exceptions_to_absorb(self, exceptions: List[BaseException]):
        """
        Silences list of provided exceptions if raised and uncaught
        """
        ExceptionHandler.set_uncaught_exceptions_to_absorb(exceptions)

    # ExceptionReporter protocol
    def report_error(
        self,
        error: Union[
            BaseException,
            tuple[
                Optional[Type[BaseException]],
                Optional[BaseException],
                Optional[TracebackType]
            ]
        ]
    ):
        """Sends the error to Sentry."""
        self._api.usage_reporting.report_error(error)
        sentry_version = Version(metadata.version("sentry-sdk"))
        if sentry_version < Version("2.0.0"):
            sentry_sdk.flush()
        else:
            sentry_sdk.get_client().flush()  # pylint: disable=no-member

    @property
    def program_name(self) -> Optional[str]:
        """Returns the name of the CLI"""
        return self._click_context.find_root().info_name

    @property
    def is_logged_in(self) -> bool:
        """Returns whether the user is logged in or not"""
        return self._api.is_user_logged_in()

    @property
    def user_tier(self) -> int:
        """Returns the Proton VPN tier"""
        return self._api.user_tier

    @property
    def user_on_free_tier(self) -> bool:
        """Returns if the current user is on free tier or not.
        """
        return self.user_tier == 0

    async def get_settings(self) -> Settings:
        """Returns general settings."""
        return await self._api.load_settings()

    async def save_feature_setting(
        self,
        feature: Feature,
        value: Union[int, bool, CustomDNS]
    ):
        """Ensures that the feature is stored to disk only
        if the subscription tier allows it.

        Args:
            feature (Feature): feature whose setting will be modified
            value: value to set for the given feature

        Raises:
            AuthenticationRequiredError: if user is not logged in
            RequiresHigherTierError: if feature requires a higher plan
        """
        if not self.is_logged_in:
            raise AuthenticationRequiredError

        settings = await self.get_settings()

        if not feature.available_on_free_tier and self.user_on_free_tier:
            raise RequiresHigherTierError

        settings = self._set_settings_by_path(settings, feature.setting_path, value)

        await self.save_settings(settings)

    async def get_feature_setting(
        self,
        feature: Feature
    ) -> Union[int, bool, CustomDNS]:
        """Retrieves the current setting for the requested feature.

        Args:
            feature (Feature): feature whose setting will be returned

        Raises:
            AuthenticationRequiredError: if user is not logged in
        """
        if not self.is_logged_in:
            raise AuthenticationRequiredError

        settings = await self.get_settings()

        return self._get_settings_by_path(settings, feature.setting_path)

    async def save_settings(self, settings: Settings):
        """Saves general settings."""
        connector = await self.get_vpn_connector()
        is_connected = connector.is_connected
        free_user_requesting_free_features =\
            self.user_on_free_tier and settings.features.are_free_tier_defaults()
        if not free_user_requesting_free_features and is_connected:
            # paying user requesting feature changes with live connection
            # wait for LA connection event confirming feature request complete
            async with _wait_for_event(connector,
                                       event_types=[ConnectionStateEnum.CONNECTED]):
                await self._api.save_settings(settings)
        else:
            await self._api.save_settings(settings)

    def _set_settings_by_path(
        self,
        settings: Settings,
        path: str,
        value: Union[int, bool, CustomDNS]
    ) -> Settings:
        parts = path.split(".")
        current = settings
        for part in parts[:-1]:
            current = getattr(current, part)

        setattr(current, parts[-1], value)
        return settings

    def _get_settings_by_path(
        self,
        settings: Settings,
        path: str
    ) -> Union[int, bool, CustomDNS]:
        parts = path.split(".")
        current = settings
        for part in parts[:-1]:
            current = getattr(current, part)

        return getattr(current, parts[-1])

    def parse_dns_ips(self, dns_list: list[str]) -> list[CustomDNSEntry]:
        """Parses a CSV string of DNS IPs into a list of strings.

        Args:
            dns_csv (str): CSV string of DNS IPs.

        Returns:
            List[str]: List of DNS IPs.

        Raises:
            ValueError: If any of the DNS IPs are invalid.
        """
        parsed_dns_list = []
        for dns in dns_list:
            try:
                parsed_dns_list.append(CustomDNSEntry.new_from_string(dns))
            except ValueError as excp:
                raise InvalidDNS(dns, excp) from excp
        return parsed_dns_list

    def to_custom_dns(self, state: bool, dns_ips: list[CustomDNSEntry]) -> CustomDNS:
        """Convert to custom dns setting object.

        Args:
            state (bool): whether is enabled or disabled
            dns_ips (list[CustomDNSEntry]): list of IPs

        Returns:
            CustomDNS: created object
        """
        return CustomDNS(state, dns_ips)

    async def get_current_connection(self) -> Optional[VPNConnection]:
        """Returns the current VPN connection or None if there isn't one."""
        return (await self.get_vpn_connector()).current_connection

    async def is_connection_active(self) -> bool:
        """
        Returns whether the current connection is active or not.

        A connection is considered active in the connecting, connected
        and disconnecting states.
        """
        return (await self.get_vpn_connector()).is_connection_active

    # pylint: disable=too-many-arguments
    async def find_logical_server(
        self,
        server_name: Optional[str] = None,
        country: Optional[str] = None,
        city: Optional[str] = None,
        features: ServerFeatureEnum = 0,
        random_server: bool = False
    ) -> Optional[LogicalServer]:
        """
        Finds a server in the serverlist meeting the user's criteria
        :param server_name: The name of the server to connect to.
        :param country: The country whose fastest/random server we want to connect to.
        :param city: The city whose fastest/random server we want to connect to.
        :param features: The required features of the fastest/random server we wish to connect to.
        :param random_server: If true, look for a random (instead of fastest) server
                       meeting all requirements.
        :return: The fastest logical server meeting the provided constraints.
        """
        if not self._api.is_user_logged_in():
            raise AuthenticationRequiredError

        free_user = self.user_tier == 0
        requesting_paying_feature =\
            (server_name or country or city or features or random_server)
        if free_user and requesting_paying_feature:
            raise RequiresHigherTierError

        logical_server = None
        server_list = await self.get_updated_server_list()

        # server name takes precedence
        if server_name:
            logical_server = server_list.get_by_name(server_name)
        else:
            servers = server_list.logicals

            # location filtering
            # check if we're looking in a city
            if city:
                servers = ServerList.get_servers_in_city(servers, city)
            # or see if we're looking in a country
            elif country:
                valid_country_code = self.validate_country_input(country)
                servers = ServerList.get_servers_in_country_code(servers, valid_country_code)

            # feature filtering
            features_excluded_by_default =\
                ServerFeatureEnum.SECURE_CORE | ServerFeatureEnum.TOR

            # don't exclude features that are explicitly requested
            features_excluded_by_default =\
                (features_excluded_by_default & features) ^ features_excluded_by_default

            servers = ServerList.get_servers_with_features(
                servers,
                request_features=features,
                exclude_features=features_excluded_by_default
            )

            # grab available servers
            servers = ServerList.get_available_servers(servers, self.user_tier)

            # random server or fastest server
            if random_server:
                filtered_servers = list(servers)
                if len(filtered_servers) > 0:
                    logical_server =\
                        random.choice(filtered_servers)  # nosec B311 # nosemgrep: gitlab.bandit.B311 # noqa: E501 # pylint: disable=line-too-long
            else:
                logical_server = ServerList.get_fastest_server(servers)

        return logical_server

    async def get_all_countries(self) -> List[Country]:
        """Returns a list of countries."""
        if not self._api.is_user_logged_in():
            raise AuthenticationRequiredError

        server_list = await self.get_updated_server_list()
        return server_list.group_by_country()

    async def connect(
        self,
        server: LogicalServer
    ) -> Optional[states.State]:
        """
        Establishes a VPN connection.
        :param server: The specified server to connect to.
        :return: Connection state on successful connection, None otherwise
        """
        if not self._api.is_user_logged_in():
            raise AuthenticationRequiredError

        # make sure our certificate hasn't expired, or isn't about to.
        # this needs to happen before we establish connection state
        # otherwise if we are in a connected/error state then we will block
        # after starting/restarting local agent listener synchronously
        await self._api.refresher.update_certificate_if_necessary()

        connector = await self.get_vpn_connector()

        if connector.is_connection_active:
            # an asynchronous connect event from local agent
            # makes it difficult to time a state machine driven disconnect and connect
            # ... So we need to separate disconnection from connection explicitly
            # to ensure we correctly time switching between servers
            await self.disconnect()

        try:
            async with _wait_for_event(connector,
                                       event_types=[ConnectionStateEnum.CONNECTED]):
                await self._connect(server)
        except (TimeoutError, VPNConnectionError):
            # If the connection fails, clean up NM setup
            await self.disconnect()

        connection_state = None
        if isinstance(connector.current_state, states.Connected):
            connection_state = connector.current_state

        return connection_state

    async def disconnect(self):
        """
        Terminates a VPN connection.
        """
        connector = await self.get_vpn_connector()
        if not isinstance(connector.current_state, states.Disconnected):
            async with _wait_for_event(connector,
                                       event_types=[ConnectionStateEnum.DISCONNECTED]):
                await self._disconnect()

    async def login(self, username: str,
                    get_password: Callable[[], str],
                    get_2fa: Callable[[], str]):
        """
        Logs the user in.
        :param username:
        :param get_password: A callable that will return the account password
        :param get_2fa: A callable that will return the two factor
            authentication token if invoked.
        """
        if self._api.is_user_logged_in():
            raise SignoutRequiredError

        password = get_password()
        login_result = await self._api.login(username, password)
        if not login_result.authenticated:
            raise AuthenticationFailedError

        try:
            while login_result.twofa_required:
                login_result = await self._api.submit_2fa_code(get_2fa())
        except ProtonAPIAuthenticationNeeded as exc:
            raise Authentication2FAFailedError from exc

    async def logout(self):
        """
        Logs the user out.
        """
        if (await self.get_vpn_connector()).is_connection_active:
            await self.disconnect()

        await self._api.logout()

    def account_info(self):
        """
        Provides information about the proton vpn accout currently logged in.
        """
        return dict(
            name=self._api.account_name
        )

    async def get_updated_server_list(self) -> ServerList:
        """Returns an always-up-to-date server list."""
        return await self._api.refresher.get_up_to_date_server_list()

    async def is_serverlist_expired(self) -> bool:
        """Returns whether the caches serverlist has expired"""
        cached_server_list = self._api.server_list
        return (cached_server_list is None
                or cached_server_list.expired
                or cached_server_list.loads_expired)

    async def get_vpn_connector(self) -> VPNConnector:
        """Return the object that handles vpn connection and disconnection"""
        vpn_connector = await self._api.get_vpn_connector()
        return vpn_connector

    def validate_country_input(
            self,
            country: str,
    ) -> str:
        """Ensures that the passed country code ISO or country name is
        a valid value.

        Args:
            country (str): country ISO code or country name in plain english.

        Raises:
            CountryCodeError: if the passed country code does not exist
            CountryNameError: if the passed country name does not exist

        Returns:
            str: returns country code for a valid country
        """
        country_code = None

        if len(country) == 2:
            # assume the user specified a country code
            country_code = validate_country_code(country)
            if not country_code:
                raise CountryCodeError
        else:
            # assume user specified a country name
            country_code = get_country_code_for_name(country)
            if not country_code:
                raise CountryNameError

        return country_code

    async def _connect(self, server: LogicalServer):
        vpn_server = (await self.get_vpn_connector()).get_vpn_server(
            server, await self._api.refresher.get_up_to_date_client_config()
        )

        settings = await self._api.load_settings()

        await (await self.get_vpn_connector()).connect(
            vpn_server,
            protocol=settings.protocol
        )

    async def _disconnect(self):
        await (await self.get_vpn_connector()).disconnect()
