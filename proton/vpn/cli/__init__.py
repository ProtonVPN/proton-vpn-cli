
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
import atexit
from importlib.metadata import version, PackageNotFoundError
import os
import signal
import sys
from typing import List, Optional

import click
from dbus_fast.aio import MessageBus
from dbus_fast import BusType, Message, MessageType

from proton.session.exceptions import ProtonAPIError, ProtonAPINotReachable
from proton.vpn.cli._cli_constants import \
    PROGRAM_NAME, \
    HELP_OPTION, \
    HELP_OPTION_ABBREVIATED
from proton.vpn.cli.commands.account import signin, signout, info
from proton.vpn.cli.commands.server import connect, disconnect, status, servers
from proton.vpn.cli.commands.location_discovery import countries, cities
from proton.vpn.cli.commands.settings import config, SETTINGS_LIST_COMMAND
from proton.vpn.cli.core.controller import Controller, Params
from proton.vpn.cli.core.run_async import run_async
from proton.vpn.cli.core.click_exception_handler import ClickExceptionHandler


try:
    __version__ = version("proton-vpn-cli")
except PackageNotFoundError:
    __version__ = "development"


# Installed during interpreter shutdown to prevent core dumps from
# Rust local_agent.abi3.so background threads that may call Python
# callbacks during Py_FinalizeEx. Logs to stderr instead of dumping
# core so the occurrence is still visible, but exits cleanly.
def _handle_shutdown_abort(_signum, _frame):
    sys.stderr.write(
        "Warning: suppressed a SIGABRT during interpreter shutdown "
        "(likely from local_agent.abi3.so background threads).\n"
    )
    os._exit(1)


def _install_abort_guard():
    signal.signal(signal.SIGABRT, _handle_shutdown_abort)


atexit.register(_install_abort_guard)


PROTON_VPN_LOGO = r"""
  ____            _               __     ______  _   _
 |  _ \ _ __ ___ | |_ ___  _ __   \ \   / /  _ \| \ | |
 | |_) | '__/ _ \| __/ _ \| '_ \   \ \ / /| |_) |  \| |
 |  __/| | | (_) | || (_) | | | |   \ V / |  __/| |\  |
 |_|   |_|  \___/ \__\___/|_| |_|    \_/  |_|   |_| \_|"""

GTK_APP_ID = "proton.vpn.app.gtk"


_CLICK_CONTEXT_SETTINGS = {"help_option_names": [HELP_OPTION, HELP_OPTION_ABBREVIATED]}


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
    help=f"\b {PROTON_VPN_LOGO} {__version__} \n\n Proton VPN command-line interface for Linux.",
    epilog=f"""\b
              Examples:
                {PROGRAM_NAME} {signin.name}                      # Sign in
                {PROGRAM_NAME} {connect.name}                     # Connect to fastest server
                {PROGRAM_NAME} {connect.name} --country US        # Connect to US
                {PROGRAM_NAME} {config.name} {SETTINGS_LIST_COMMAND: <20} # View settings
                {PROGRAM_NAME} {disconnect.name}                  # Disconnect
              \b
              Quick Start:
                1. Sign in:    {PROGRAM_NAME} {signin.name}
                2. Connect:    {PROGRAM_NAME} {connect.name}
                3. Disconnect: {PROGRAM_NAME} {disconnect.name}
              \b
              Get Command Help:
                {PROGRAM_NAME} [command] --help
              \b
              Documentation:
                https://protonvpn.com/support/linux-cli
              \b
              Support:
                https://protonvpn.com/support-form
                support@protonvpn.com"""
)
@click.option(
    '-v',
    '--verbose',
    help="Show detailed output during command execution",
    is_flag=True,
    default=False)
@click.pass_context
@run_async
async def app(ctx, verbose):
    """Groups all CLI commands"""
    ctx.obj.verbose = verbose
    if not ctx.obj.allow_gui_concurrency:
        command_help_requested = _is_help_requested()
        vpn_gui_running = await _vpn_gui_running()
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
app.add_command(disconnect)
app.add_command(status)
app.add_command(servers)

# listing functionality
app.add_command(countries)
app.add_command(cities)

# set features
app.add_command(config)


def main(
    allow_concurrency: bool = False,
    cli_args: Optional[List[str]] = None,
    controller: Optional[Controller] = None
):
    """Runs the CLI."""
    try:
        # pylint: disable=E1120
        app(
            obj=Params(
                allow_gui_concurrency=allow_concurrency,
                overriding_controller=controller
            ),
            standalone_mode=False,
            args=cli_args
        )
    except ProtonAPIError as exc:
        click.echo(f"Error: {exc.message}", err=True)
        sys.exit(1)
    except (TimeoutError, ProtonAPINotReachable):
        click.echo(
            "Error: Network connectivity issues detected. "
            "Please check your internet connection and try again."
        )
        sys.exit(1)
    except click.Abort:
        click.echo("Abort!", err=True)
        sys.exit(1)
    except Exception as exc:
        if isinstance(exc, click.exceptions.ClickException):
            if ClickExceptionHandler.handle_error(exc):
                sys.exit(exc.exit_code)

        click.echo(
            "An unexpected error occurred. Please try again.\n"
            "If the error persists please contact customer support: "
            "https://protonvpn.com/support/contact?"
            "subject=%5BCLI%5D&os=Linux&platform=VPN%20for%20Linux"
        )
        raise  # make sure it gets reported to sentry
