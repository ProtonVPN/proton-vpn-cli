"""
Server/Connection related commands.

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
from asyncio import CancelledError
from typing import Optional

import click

from proton.vpn.cli._cli_constants import PROGRAM_NAME
from proton.vpn.cli.core.exceptions import \
    AuthenticationRequiredError, \
    CountryCodeError, \
    CountryNameError, \
    RequiresHigherTierError, \
    VPNConnection2FARequiredError
from proton.vpn.cli.core.run_async import run_async
from proton.vpn.cli.core.controller import Controller, DEFAULT_CLI_NAME
from proton.vpn.cli.core.wait_for_current_tasks import wait_for_current_tasks
from proton.vpn.session.exceptions import ServerNotFoundError
from proton.vpn.session.servers.types import LogicalServer, ServerFeatureEnum
from proton.vpn.cli.commands.account import SIGNIN_COMMAND
from proton.vpn.cli.commands.feature_setting_definitions import \
    OPENVPN_TCP, \
    OPENVPN_UDP
from proton.vpn.cli.commands.command_utils import \
    inform_that_expired_serverlist_will_be_updated_if_necessary

CONNECT_COMMAND = "connect"
DISCONNECT_COMMAND = "disconnect"
STATUS_COMMAND = "status"
SERVERLIST_COMMAND = "servers"
SERVER_NAME_ARGUMENT = "SERVER_NAME"


class FailedConnection(click.ClickException):
    """When attempting to establish a connection, it fails
    """


def _print_usage_error(msg: str):
    raise click.UsageError(msg)


@click.command(
    name=CONNECT_COMMAND,
    epilog=f"""\b
Examples:
  # Quick connection
  {PROGRAM_NAME} {CONNECT_COMMAND}                     # Fastest server globally
\b
  # Location selection
  {PROGRAM_NAME} {CONNECT_COMMAND} --country US        # Fastest in United States
  {PROGRAM_NAME} {CONNECT_COMMAND} --city "New York"   # Fastest in New York
  {PROGRAM_NAME} {CONNECT_COMMAND} IT#23               # Specific server
\b
  # Feature-based selection
  {PROGRAM_NAME} {CONNECT_COMMAND} --p2p               # Fastest P2P server
  {PROGRAM_NAME} {CONNECT_COMMAND} --country IT --p2p  # Fastest P2P in Italy
\b
  # Extra secure connections
  {PROGRAM_NAME} {CONNECT_COMMAND} --securecore        # Secure Core routing
  {PROGRAM_NAME} {CONNECT_COMMAND} --tor               # Tor over VPN"""
)
@click.pass_context
@click.argument(SERVER_NAME_ARGUMENT, required=False)
@click.option(
    "--country",
    default=None,
    help="""\b
            Connect to fastest server in specified country
            Country code (US, GB, DE) or full name ("United States")""")
@click.option(
    "--city",
    default=None,
    help="""\b
            Connect to fastest server in specified city
            City name (use quotes for multi-word: \"New York\")""")
@click.option('--p2p', is_flag=True, help="Connect to fastest P2P-optimized server")
@click.option("-sc", "--securecore", is_flag=True, help="Connect to fastest Secure Core server")
@click.option("--tor", is_flag=True, help="Connect to fastest Tor server")
@click.option("--random", is_flag=True, help="Connect to random available server")
@run_async
# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
# pylint: disable=too-many-branches
async def connect(
    ctx,
    server_name: Optional[str],
    city: Optional[str],
    country: Optional[str],
    p2p: bool,
    securecore: bool,
    tor: bool,
    random: bool
):
    """
    Connect to Proton VPN server.

    Arguments:

    SERVER_NAME Connect to specific server by ID (e.g., IT#23)
    """
    controller = await Controller.create(params=ctx.obj, click_ctx=ctx)
    # Silence cancelled exceptions raised by tasks we don't need to wait for after connection.
    # For example, some tasks are usually created to process a second Connected state broadcasted
    # to signal that the VPN server successfully applied the requested connection features.
    controller.set_uncaught_exceptions_to_absorb([CancelledError])
    server = None
    connection_state = None
    requested_features = _compose_requested_features(p2p, securecore, tor)

    await inform_that_expired_serverlist_will_be_updated_if_necessary(controller)

    # attempt to find a satisfactory server, and connect to it
    try:
        server = await controller.find_logical_server(
            server_name,
            country,
            city,
            requested_features,
            random
        )
        if not server:
            _print_usage_error("No servers found matching criteria. Try broadening your filters.")
            return

        connection_state = await controller.connect(server)

    except AuthenticationRequiredError:
        _print_usage_error(
            "Authentication required."
            f"Please sign in with '{controller.program_name} {SIGNIN_COMMAND}' before connecting."
        )
    except ServerNotFoundError as excp:
        if server_name:
            msg = f"Invalid server ID '{server_name}'. " \
                  "Please use a valid server ID from the server list."
        elif city:
            msg = f"City '{city}' not found or no servers available."
        else:
            msg = str(excp)

        _print_usage_error(msg)
    except CountryCodeError:
        _print_usage_error(f"Invalid country code '{country}'. Please use a valid country code.")
    except CountryNameError:
        _print_usage_error(f"Invalid country name '{country}'. Please use a valid country name.")
    except RequiresHigherTierError:
        free_user = controller.user_tier == 0
        if free_user:
            _display_free_user_limitation(
                controller,
                server_name,
                city,
                country,
                requested_features,
                random
            )
    except VPNConnection2FARequiredError as exc:
        raise click.ClickException(
            "2FA Required: You are connected to the VPN, but all traffic is blocked.\n"
            "You need to go to the authentication page provided by security and authenticate"
            " with your hardware key.\nAfter that, the traffic will be enabled."
        ) from exc

    if connection_state:
        # notify user of successful connection and server details
        current_connection = connection_state.context.connection
        connection_details = connection_state.context.event.context.connection_details
        server_ip = connection_details.server_ipv4 if connection_details else None
        click.echo(
            f"Connected to {current_connection.server_name} "
            f"in {_get_most_specific_server_location(server)}. "
        )
        if server_ip:
            click.echo(f"Your new IP address is {server_ip}.")

        await _display_relevant_server_capabilities(controller, server)

        protocol = (await controller.get_settings()).protocol
        _display_openvpn_warning_if_necessary(protocol)
    elif server:
        # we found a server but the connection failed
        raise FailedConnection(
            "Connection failed. "
            "Try connecting to a different server or check your network settings."
        )


@click.command(
    name=DISCONNECT_COMMAND,
    epilog=f"""\b
Examples:
  {PROGRAM_NAME} {DISCONNECT_COMMAND}
\b
Check connection status:
  {PROGRAM_NAME} {STATUS_COMMAND}"""
)
@click.pass_context
@run_async
async def disconnect(ctx):
    """Disconnect from current VPN server.

        \b
        This command will:
          - Terminate active VPN connection
          - Restore original network configuration"""
    controller = await Controller.create(params=ctx.obj, click_ctx=ctx)
    await controller.disconnect()
    click.echo("Disconnected.")

    # wait for post-disconnect notification killswitch implementation setting
    await wait_for_current_tasks()


@click.command(
    name=STATUS_COMMAND,
    epilog=f"""\b
            Examples:
              {PROGRAM_NAME} {STATUS_COMMAND}"""
)
@click.pass_context
@run_async
async def status(ctx):
    """\b
    Show current VPN connection status.
    \b
    Displays:
      - Connection status (Connected/Disconnected)
      - Server name and location (if connected)
      - Server load percentage (if connected)
      - Connection protocol (if connected)
    """
    controller = await Controller.create(params=ctx.obj, click_ctx=ctx)
    connection = (await controller.get_vpn_connector()).current_state.context.connection
    server_name = connection.server_name if connection else None
    status_lines = []
    if server_name:
        await inform_that_expired_serverlist_will_be_updated_if_necessary(controller)
        server_list = await controller.get_updated_server_list()
        server = server_list.get_by_name(server_name)
        server_location = _get_most_specific_server_location(server)
        status_lines.extend([
            "Status: Connected",
            f"Server: {server_name} in {server_location}",
            f"Load: {server.load}%",
            f"Protocol: {connection.protocol}"
        ])
    else:
        status_lines.extend([
            "Status: Disconnected"
        ])

    click.echo("\n".join(status_lines))


@click.command(
    name=SERVERLIST_COMMAND,
)
@run_async
async def servers():
    """
    View available servers. Prints the link to the full server list on protonvpn.com.
    """
    click.echo("To view detailed server information including specific server IDs, "
               "visit:  https://account.proton.me/vpn/WireGuard")


def _get_most_specific_server_location(server: LogicalServer) -> str:
    has_secure_core = ServerFeatureEnum.SECURE_CORE in server.features
    if has_secure_core and server.city:
        return f"{server.city}, via {server.entry_country_name}"

    if server.city:
        return f"{server.city}, {server.entry_country_name}"

    return server.entry_country_name


async def _display_relevant_server_capabilities(
    controller: Controller,
    server: LogicalServer
):
    settings = await controller.get_settings()
    if settings.features.port_forwarding:
        port_forwarding_enabled_server = ServerFeatureEnum.P2P in server.features
        if port_forwarding_enabled_server:
            click.echo(
                "\nPort forwarding is active on this server.\n"
                "To get your forwarded port, run the natpmpc setup script.\n"
                "Guide: https://protonvpn.com/support/port-forwarding-manual-setup#linux"
            )
        else:
            click.echo(
                "\nNote: Port forwarding is enabled but this server does not support it.\n"
                "Connect to a P2P server to use port forwarding:"
                f"{controller.program_name} {CONNECT_COMMAND} --p2p"
            )


def _display_openvpn_warning_if_necessary(protocol: str):
    if protocol in [OPENVPN_UDP, OPENVPN_TCP]:
        click.echo(
            "\nOpenVPN is not fully supported in CLI and you may experience instability. "
            "For best results, use WireGuard."
        )


def _compose_requested_features(
    p2p: bool,
    securecore: bool,
    tor: bool
) -> ServerFeatureEnum:
    requested_features: ServerFeatureEnum = 0
    if p2p:
        requested_features |= ServerFeatureEnum.P2P
    if securecore:
        requested_features |= ServerFeatureEnum.SECURE_CORE
    if tor:
        requested_features |= ServerFeatureEnum.TOR

    return requested_features


# pylint: disable=too-many-arguments
def _display_free_user_limitation(
    controller: Controller,
    server_name: Optional[str],
    city: Optional[str],
    country: Optional[str],
    requested_features: Optional[ServerFeatureEnum],
    random: bool
):
    free_user = controller.user_tier == 0
    if not free_user:
        return

    # when specifying a server name, the user requires a paying tier
    if server_name:
        proton_cli_name = controller.program_name or DEFAULT_CLI_NAME
        _print_usage_error(
            f"Server selection by ID is not available on the free plan."
            f" Please use '{proton_cli_name} {CONNECT_COMMAND}' to connect "
            "to available free servers or upgrade to access all servers."
        )
        return

    # when specifying a country or city, the user requires a paying tier
    if country or city:
        proton_cli_name = controller.program_name or DEFAULT_CLI_NAME
        _print_usage_error(
            "Location selection is not available on the free plan. "
            f"Please use '{proton_cli_name} {CONNECT_COMMAND}' to connect "
            "to available free servers or upgrade to choose your location."
        )
        return

    # when specifying a server feature, the user requires a paying tier
    requested_feature_type = None
    if requested_features & ServerFeatureEnum.P2P != 0:
        requested_feature_type = "P2P"
    elif requested_features & ServerFeatureEnum.SECURE_CORE != 0:
        requested_feature_type = "Secure Core"
    elif requested_features & ServerFeatureEnum.TOR != 0:
        requested_feature_type = "Tor"

    if requested_feature_type:
        proton_cli_name = controller.program_name or DEFAULT_CLI_NAME
        _print_usage_error(
            f"{requested_feature_type} servers are not available on the free plan. "
            f"Please use '{proton_cli_name} {CONNECT_COMMAND}' to connect "
            "to available free servers "
            f"or upgrade to to access {requested_feature_type} servers."
        )
        return

    # when requesting a random server, the user requires a paying tier
    if random:
        proton_cli_name = controller.program_name or DEFAULT_CLI_NAME
        _print_usage_error(
            "Random selection is not available on the free plan. "
            f"Please use '{proton_cli_name} {CONNECT_COMMAND}' "
            "to connect to available free servers."
        )
        return
