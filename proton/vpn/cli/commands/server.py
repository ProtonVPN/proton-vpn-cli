
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

import click
from json import loads, dumps
from pathlib import Path
from asyncio import CancelledError
from typing import Optional

from proton.vpn.cli.core.exceptions import \
    AuthenticationRequiredError, \
    CountryCodeError, \
    CountryNameError, \
    RequiresHigherTierError
from proton.vpn.cli.core.run_async import run_async
from proton.vpn.cli.core.controller import Controller, DEFAULT_CLI_NAME
from proton.vpn.cli.core.wait_for_current_tasks import wait_for_current_tasks
from proton.vpn.session.exceptions import ServerNotFoundError
from proton.vpn.session.servers.types import LogicalServer, ServerFeatureEnum
from proton.vpn.cli.commands.account import SIGNIN_COMMAND
from proton.vpn.connection import events
from proton.vpn.cli.commands.command_utils import \
    inform_that_expired_serverlist_will_be_updated_if_necessary


TMP_FILE = Path("/tmp/protonvpn-connectiondetails.json")


class FailedConnection(click.ClickException):
    """When attempting to establish a connection, it fails
    """


def _print_usage_error(msg: str):
    raise click.UsageError(msg)


@click.command()
@click.pass_context
@click.argument("server_name", required=False)
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
            City name (use quotes for multi-word: "New York", "Los Angeles")""")
@click.option('--p2p', is_flag=True, help="Connect to the fastest P2P-optimized server")
@click.option("-sc", "--securecore", is_flag=True, help="Connect to the fastest Secure Core server")
@click.option("--tor", is_flag=True, help="Connect to the fastest Tor server")
@click.option("--random", is_flag=True, help="Connect to a random available server")
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
    """Connect to Proton VPN"""
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
            TMP_FILE.write_text(
                dumps(connection_state.context.event.context.connection_details),
                encoding="utf-8"
            )

        protocol = (await controller.get_settings()).protocol
        _display_openvpn_warning_if_necessary(protocol)
    elif server:
        # we found a server but the connection failed
        raise FailedConnection(
            "Connection failed. "
            "Try connecting to a different server or check your network settings."
        )


CONNECT_COMMAND = connect.name


@click.command()
@click.pass_context
@click.option("-j", "--json", is_flag=True, help="Dump status as JSON")
@click.option("-s", "--simple", is_flag=True, help="Print simple status to stdout, useful for i3bar or polybar.")
@run_async
async def status(ctx, json: bool = False, simple: bool = False):
    """Get status from Proton VPN"""
    controller = await Controller.create(params=ctx.obj, click_ctx=ctx)
    connector = await controller.get_vpn_connector()
    connection = connector.current_connection

    # Bail early if disconnected.
    if connection is None:
        print("ProtonVPN: Disconnected")
        return

    server = await controller.find_logical_server(connection.server_name)
    state = connector.current_state

    # Bail early if disconnected.
    if state is None:
        print("ProtonVPN: Disconnected")
        return

    # _Try_ to get connection details... sometimes it's not populated though???
    connection_details = state.context.event.context.connection_details

    # If it's not populated, read from tmp file on disk, if we can
    try:
        connection_details = connection_details or events.ConnectionDetails(
            **loads(TMP_FILE.read_text(encoding="utf-8"))
        )
    except OSError, TypeError:
        # Either the file wasn't there, permissions were bad, or the json was not in an expected format / malformed
        pass

    status = {
        "exit": {
            "city": server.city,
            "country": server.exit_country,
            "name": connection.server_name,
            "ipv4": getattr(connection_details, "server_ipv4", ""),
            "ipv6": getattr(connection_details, "server_ipv6", "")
        },
        "entry": {
            "country": server.entry_country,
            "ip": connection.server_ip,
            "name": connection.server_name,
            "client": {
                "ip": getattr(connection_details, "device_ip", ""),
                "country": getattr(connection_details, "device_country", "")
            }
        },
    }

    if json:
        return dumps(status)

    elif simple:
        _ip = status["exit"].get("ipv4", "")
        click.echo(
            f"ProtonVPN: {status["exit"]["name"]}"
            f"{f" ({_ip})" if _ip else ""}"
        )
        return status

    else:
        click.echo(
            f"Connected to {status["exit"]["name"]} "
            f"in {_get_most_specific_server_location(server)}. "
            f"Your new IP address is {status["exit"].get("ipv4", "Unknown")}."
        )
        # print(status)
        return status


@click.command()
@click.pass_context
@run_async
async def disconnect(ctx):
    """Disconnect from Proton VPN"""
    controller = await Controller.create(params=ctx.obj, click_ctx=ctx)
    await controller.disconnect()

    # wait for post-disconnect notification killswitch implementation setting
    await wait_for_current_tasks()


def _get_most_specific_server_location(server: LogicalServer) -> str:
    has_secure_core = ServerFeatureEnum.SECURE_CORE in server.features
    if has_secure_core and server.city:
        return f"{server.city}, via {server.entry_country_name}"

    if server.city:
        return f"{server.city}, {server.entry_country_name}"

    return server.entry_country_name


OPENVPN_UDP = "openvpn-udp"
OPENVPN_TCP = "openvpn-tcp"


def _display_openvpn_warning_if_necessary(protocol: str):
    if protocol in [OPENVPN_UDP, OPENVPN_TCP]:
        click.echo(
            "OpenVPN is not fully supported in CLI and you may experience instability. "
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

    # when requested a random server, the user requires a paying tier
    if random:
        proton_cli_name = controller.program_name or DEFAULT_CLI_NAME
        _print_usage_error(
            "Random selection is not available on the free plan. "
            f"Please use '{proton_cli_name} {CONNECT_COMMAND}' "
            "to connect to available free servers."
        )
        return
