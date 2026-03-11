"""
Copyright (c) 2026 Proton AG

Provides CLI command testing for server connection and filtering.

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
from typing import Optional
from unittest.mock import AsyncMock, Mock, PropertyMock
import pytest

import click
from click.testing import CliRunner

from proton.vpn.cli import app as app_cmd
from proton.vpn.cli.commands.account import SIGNIN_COMMAND
from proton.vpn.cli.commands.server import CONNECT_COMMAND, STATUS_COMMAND
from proton.vpn.cli.core.exceptions import \
    AuthenticationRequiredError, \
    CountryCodeError, \
    CountryNameError, \
    RequiresHigherTierError
from proton.vpn.session.exceptions import ServerNotFoundError
from proton.vpn.session.servers.types import ServerFeatureEnum


@pytest.mark.parametrize("server_list_expired", [True, False])
def test_connect_notifies_of_serverlist_update_when_expired(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock,
    server_list_expired: bool
):
    controller_mock.is_serverlist_expired.return_value = server_list_expired

    result = runner.invoke(
        app_cmd,
        [CONNECT_COMMAND, "server_name"],
        parent=test_context
    )

    assert ("Server list is outdated, updating... This may take a moment."
            in result.output) == server_list_expired


def test_connect_fails_with_suggestion_to_relax_filter_constraints_when_no_server_found(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    controller_mock.find_logical_server.return_value = None

    result = runner.invoke(
        app_cmd,
        [CONNECT_COMMAND, "server_name"],
        parent=test_context
    )

    assert result.exit_code == 2
    assert "No servers found matching criteria. Try broadening your filters."\
        in result.output


def test_connect_fails_when_not_signed_in(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    def find_logical_server(*_):
        raise AuthenticationRequiredError

    controller_mock.find_logical_server.side_effect = find_logical_server

    result = runner.invoke(
        app_cmd,
        [CONNECT_COMMAND, "server_name"],
        parent=test_context
    )

    assert result.exit_code == 2
    assert \
        "Authentication required."\
        f"Please sign in with '{test_context.info_name} {SIGNIN_COMMAND}' before connecting."\
        in result.output


@pytest.mark.parametrize(
    "server_name, city, country",
    [
        ("invalid-server-id", None, None),
        ("invalid-server-id", "New York", "US"),
        (None, "New York", None),
        (None, "New York", "US"),
        (None, None, "US"),
    ],
)
def test_connect_fails_with_correct_message_when_server_not_found(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock,
    server_name: str,
    city: str,
    country: str
):
    def find_logical_server(*_):
        raise ServerNotFoundError("No server available in the current tier")

    controller_mock.find_logical_server.side_effect = find_logical_server

    args = [CONNECT_COMMAND]
    if server_name is not None:
        args.append(server_name)
    if city is not None:
        args.extend(["--city", city])
    if country is not None:
        args.extend(["--country", country])

    result = runner.invoke(
        app_cmd,
        args,
        parent=test_context
    )

    assert result.exit_code == 2
    if server_name:
        assert f"Invalid server ID '{server_name}'. "\
               "Please use a valid server ID from the server list." in result.output
    elif city:
        assert f"City '{city}' not found or no servers available." in result.output
    else:
        assert "No server available in the current tier" in result.output


def test_connect_fails_when_provided_invalid_country_code(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    def find_logical_server(*_):
        raise CountryCodeError

    controller_mock.find_logical_server.side_effect = find_logical_server

    result = runner.invoke(
        app_cmd,
        [CONNECT_COMMAND,
         "server_name",
         "--country",
         "not_a_country_code"],
        parent=test_context
    )

    assert result.exit_code == 2
    assert "Invalid country code 'not_a_country_code'. Please use a valid country code."\
        in result.output


def test_connect_fails_when_provided_invalid_country_name(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    def find_logical_server(*_):
        raise CountryNameError

    controller_mock.find_logical_server.side_effect = find_logical_server

    result = runner.invoke(
        app_cmd,
        [CONNECT_COMMAND,
         "server_name",
         "--country",
         "not_a_country_name"],
        parent=test_context
    )

    assert result.exit_code == 2
    assert "Invalid country name 'not_a_country_name'. Please use a valid country name."\
        in result.output


@pytest.mark.parametrize(
    "server_name, city, country, features, printable_feature_type, random",
    [
        ("invalid-server-id", None, None, "--p2p", "P2P", "--random"),
        ("invalid-server-id", "New York", "US", "--p2p", "P2P", "--random"),
        (None, "New York", None, "--p2p", "P2P", "--random"),
        (None, "New York", "US", "--p2p", "P2P", "--random"),
        (None, None, "US", "--p2p", "P2P", "--random"),
        (None, None, None, "--securecore", "Secure Core", "--random"),
        (None, None, None, "-sc", "Secure Core", "--random"),
        (None, None, None, "--tor", "Tor", "--random"),
        (None, None, None, "--p2p", "P2P", "--random"),
        (None, None, None, None, None, "--random"),
    ],
)
def test_connect_fails_when_requested_features_require_higher_tier(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock,
    server_name: str,
    city: str,
    country: str,
    features: str,
    printable_feature_type: str,
    random: str,
):
    def find_logical_server(*_):
        raise RequiresHigherTierError

    controller_mock.find_logical_server.side_effect = find_logical_server
    type(controller_mock).user_tier = PropertyMock(return_value=0)  # free user

    args = [CONNECT_COMMAND]
    if server_name is not None:
        args.append(server_name)
    if city is not None:
        args.extend(["--city", city])
    if country is not None:
        args.extend(["--country", country])
    if features is not None:
        args.append(features)
    if random is not None:
        args.append(random)

    result = runner.invoke(
        app_cmd,
        args,
        parent=test_context
    )

    if server_name:
        assert f"Server selection by ID is not available on the free plan."\
               f" Please use '{test_context.info_name} {CONNECT_COMMAND}' to connect "\
               "to available free servers or upgrade to access all servers."\
               in result.output
    elif country or city:
        assert "Location selection is not available on the free plan. "\
               f"Please use '{test_context.info_name} {CONNECT_COMMAND}' to connect "\
               "to available free servers or upgrade to choose your location."\
               in result.output
    elif features:
        assert f"{printable_feature_type} servers are not available on the free plan. "\
               f"Please use '{test_context.info_name} {CONNECT_COMMAND}' to connect "\
               "to available free servers "\
               f"or upgrade to to access {printable_feature_type} servers."\
               in result.output
    elif random:
        assert "Random selection is not available on the free plan. "\
               f"Please use '{test_context.info_name} {CONNECT_COMMAND}' "\
               "to connect to available free servers."\
               in result.output

    assert result.exit_code == 2


@pytest.mark.parametrize(
    "ip_address, has_secure_core, has_city",
    [
        ("1.1.1.1", True, True),
        (None, True, True),
        (None, False, True),
        ("2.2.2.2", False, False)
    ]
)
def test_connect_notifies_when_successfully_connected(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock,
    ip_address: Optional[str],
    has_secure_core: bool,
    has_city: bool
):
    server_mock = Mock()
    server_mock.entry_country_name = "COUNTRY"
    server_mock.city = "city" if has_city else None
    server_mock.features = ServerFeatureEnum.SECURE_CORE if has_secure_core else []

    def find_logical_server(*_):
        return server_mock

    connection_state_mock = Mock()
    connection_state_mock.context.connection.server_name = "server_id"
    connection_state_mock.context.event.context.connection_details.server_ipv4 = ip_address

    def connect(*_):
        return connection_state_mock

    controller_mock.find_logical_server.side_effect = find_logical_server
    controller_mock.connect.side_effect = connect

    result = runner.invoke(
        app_cmd,
        [CONNECT_COMMAND, "server_id"],
        parent=test_context
    )

    assert result.exit_code == 0

    assert f"Connected to {connection_state_mock.context.connection.server_name} "\
        in result.output

    if has_city:
        if has_secure_core:
            assert f"in {server_mock.city}, via {server_mock.entry_country_name}"\
                in result.output
        else:
            assert f"in {server_mock.city}, {server_mock.entry_country_name}" in result.output
    else:
        assert f"in {server_mock.entry_country_name}" in result.output

    if ip_address:
        assert f"Your new IP address is {ip_address}." in result.output


@pytest.mark.parametrize(
    "port_forwarding_enabled, server_supports_port_forwarding", 
    [
        (True, True),
        (True, False),
        (False, True),
        (False, False),
    ]
)
def test_connect_notifies_of_port_forwarding_server_capabilities_when_successfully_connected(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock,
    port_forwarding_enabled: bool,
    server_supports_port_forwarding: bool
):
    def find_logical_server(*_):
        server_mock = Mock()
        server_mock.features = \
            [ServerFeatureEnum.P2P] if server_supports_port_forwarding else []
        return server_mock

    def get_settings(*_):
        settings_mock = AsyncMock()
        settings_mock.features.port_forwarding = port_forwarding_enabled
        return settings_mock

    controller_mock.get_settings.side_effect = get_settings
    controller_mock.find_logical_server.side_effect = find_logical_server

    result = runner.invoke(
        app_cmd,
        [CONNECT_COMMAND, "server_id"],
        parent=test_context
    )

    assert result.exit_code == 0
    assert \
        ("\nPort forwarding is active on this server.\n"
         "To get your forwarded port, run the natpmpc setup script.\n"
         "Guide: https://protonvpn.com/support/port-forwarding-manual-setup#linux"
         in result.output) \
        == (port_forwarding_enabled and server_supports_port_forwarding)

    assert \
        ("\nNote: Port forwarding is enabled but this server does not support it.\n"
         "Connect to a P2P server to use port forwarding:"
         f"{test_context.info_name} {CONNECT_COMMAND} --p2p" in result.output) \
        == (port_forwarding_enabled and not server_supports_port_forwarding)


@pytest.mark.parametrize(
    "protocol, supported",
    [
        ("openvpn-udp", False),
        ("openvpn-tcp", False),
        ("wireguard", True)
    ]
)
def test_connect_warns_when_using_unsupported_protocol(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock,
    protocol: str,
    supported: bool
):
    def get_settings(*_):
        settings_mock = AsyncMock()
        settings_mock.protocol = protocol
        return settings_mock

    controller_mock.get_settings.side_effect = get_settings

    result = runner.invoke(
        app_cmd,
        [CONNECT_COMMAND, "server_name"],
        parent=test_context
    )

    assert result.exit_code == 0

    warning = "OpenVPN is not fully supported in CLI and you may experience instability. "\
              "For best results, use WireGuard."

    if not supported:
        assert warning in result.output
    else:
        assert warning not in result.output


def test_connect_fails_with_error_when_server_connection_fails(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    def connect(*_):
        return None

    controller_mock.connect.side_effect = connect

    result = runner.invoke(
        app_cmd,
        [CONNECT_COMMAND, "server_name"],
        parent=test_context
    )

    assert result.exit_code == 1

    assert "Connection failed. "\
           "Try connecting to a different server or check your network settings."\
        in result.output


def test_status_shows_disconnected_when_no_connection(
    controller_mock: AsyncMock,
    cli_invoke
):
    vpn_connector_mock = Mock()
    vpn_connector_mock.current_state.context.connection = None
    controller_mock.get_vpn_connector.return_value = vpn_connector_mock

    result = cli_invoke([STATUS_COMMAND])

    assert result.exit_code == 0
    assert "Status: Disconnected" in result.output
    assert "Status: Connected" not in result.output


def test_status_shows_connected_with_server_details(
    controller_mock: AsyncMock,
    cli_invoke
):
    connection_mock = Mock()
    connection_mock.server_name = "CH#1"
    connection_mock.protocol = "wireguard"
    vpn_connector_mock = Mock()
    vpn_connector_mock.current_state.context.connection = connection_mock
    controller_mock.get_vpn_connector.return_value = vpn_connector_mock

    server_mock = Mock()
    server_mock.load = 42
    server_list_mock = Mock()
    server_list_mock.get_by_name.return_value = server_mock
    controller_mock.get_updated_server_list.return_value = server_list_mock

    result = cli_invoke([STATUS_COMMAND])

    assert result.exit_code == 0
    assert "Status: Connected" in result.output
    assert "Server: CH#1" in result.output
    assert "Load: 42" in result.output
    assert "Protocol: wireguard" in result.output


@pytest.mark.parametrize("server_list_expired", [True, False])
def test_status_notifies_of_serverlist_update_when_expired(
    controller_mock: AsyncMock,
    server_list_expired: bool,
    cli_invoke
):
    controller_mock.is_serverlist_expired.return_value = server_list_expired

    connection_mock = Mock()
    connection_mock.server_name = "CH#1"
    connection_mock.protocol = "wireguard"
    vpn_connector_mock = Mock()
    vpn_connector_mock.current_state.context.connection = connection_mock
    controller_mock.get_vpn_connector.return_value = vpn_connector_mock

    server_mock = Mock()
    server_mock.load = 42
    server_list_mock = Mock()
    server_list_mock.get_by_name.return_value = server_mock
    controller_mock.get_updated_server_list.return_value = server_list_mock

    result = cli_invoke([STATUS_COMMAND])

    assert ("Server list is outdated, updating... This may take a moment."
            in result.output) == server_list_expired
