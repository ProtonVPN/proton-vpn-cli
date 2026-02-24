
"""
Proton VPN Linux CLI entry point.

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
from importlib.metadata import version, PackageNotFoundError
import sys

import click
from dbus_fast.aio import MessageBus
from dbus_fast import BusType, Message, MessageType


from proton.vpn.cli.commands.account import signin, signout, info
from proton.vpn.cli.commands.server import connect, disconnect, status
from proton.vpn.cli.commands.location_discovery import countries, cities
from proton.vpn.cli.commands.set import config
from proton.vpn.cli.core.controller import Params

try:
    __version__ = version("proton-vpn-cli")
except PackageNotFoundError:
    __version__ = "development"

PROTON_VPN_LOGO = r"""
  ____            _               __     ______  _   _
 |  _ \ _ __ ___ | |_ ___  _ __   \ \   / /  _ \| \ | |
 | |_) | '__/ _ \| __/ _ \| '_ \   \ \ / /| |_) |  \| |
 |  __/| | | (_) | || (_) | | | |   \ V / |  __/| |\  |
 |_|   |_|  \___/ \__\___/|_| |_|    \_/  |_|   |_| \_|"""

GTK_APP_ID = "proton.vpn.app.gtk"


async def _vpn_gui_running() -> bool:
    bus = await MessageBus(bus_type=BusType.SESSION).connect()

    reply = await bus.call(
        Message(
            destination="org.freedesktop.DBus",
            path="/org/freedesktop/DBus",
            interface="org.freedesktop.DBus",
            member="ListNames",
        )
    )

    if reply.message_type == MessageType.ERROR:
        return False

    session_bus_names = reply.body[0]
    return GTK_APP_ID in session_bus_names


_CLICK_CONTEXT_SETTINGS = {"help_option_names": ['-h', '--help']}


def _is_help_requested() -> bool:
    for help_flag in _CLICK_CONTEXT_SETTINGS["help_option_names"]:
        if help_flag in sys.argv:
            return True

    return False


class _OrderedGroup(click.Group):
    """OrderedGroup lists commands in the order that they were added"""
    def list_commands(self, ctx):
        return self.commands


@click.group(
    cls=_OrderedGroup,
    context_settings=_CLICK_CONTEXT_SETTINGS,
    help=f"\b {PROTON_VPN_LOGO} {__version__}",
    epilog="""\b
              NEED HELP?
              Report issues:  https://protonvpn.com/support-form""")
@click.option(
    '-v',
    '--verbose',
    help="Show detailed output during command execution",
    is_flag=True,
    default=False)
@click.pass_context
def app(ctx, verbose):
    """Groups all CLI commands"""
    ctx.obj.verbose = verbose
    command_help_requested = _is_help_requested()
    vpn_gui_running = asyncio.run(_vpn_gui_running())
    if not command_help_requested and vpn_gui_running:
        click.echo("Error: Proton VPN desktop app is currently running\n"
                   "The CLI and GUI cannot run simultaneously. "
                   "Please close the GUI application and try again.")
        ctx.exit()


# account related functionality
app.add_command(signin)
app.add_command(signout)
app.add_command(info)

# server related functionality
app.add_command(connect)
app.add_command(status)
app.add_command(disconnect)

# listing functionality
app.add_command(countries)
app.add_command(cities)

# set features
app.add_command(config)


def main():
    """Runs the CLI."""
    asyncio.run(app(obj=Params()))  # pylint: disable=E1120
