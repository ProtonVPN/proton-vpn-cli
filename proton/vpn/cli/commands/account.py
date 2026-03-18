
"""
Account/Authentication related commands.

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
import getpass

import click

from proton.vpn.cli._cli_constants import PROGRAM_NAME
from proton.vpn.cli.core.controller import Controller
from proton.vpn.cli.core.exceptions import \
    Authentication2FAFailedError, \
    AuthenticationFailedError, \
    SignoutRequiredError
from proton.vpn.cli.core.run_async import run_async


SIGNIN_COMMAND = "signin"
SIGNOUT_COMMAND = "signout"


@click.command(
    name=SIGNIN_COMMAND,
    epilog=f"""\b
           Examples:
             {PROGRAM_NAME} {SIGNIN_COMMAND} user@proton.me"""
)
@click.argument('username')
@click.pass_context
@run_async
async def signin(ctx, username: str):
    """
    Sign in to Proton VPN with your credentials.

    Arguments:

    USERNAME Proton account username
    """
    controller = await Controller.create(params=ctx.obj, click_ctx=ctx)
    try:
        await controller.login(
            username,
            getpass.getpass,
            lambda: getpass.getpass("2FA Token: ")
        )
        click.echo(f"Successfully signed in as '{controller.account_name}'")
    except SignoutRequiredError as exc:
        raise click.ClickException(
            "Already signed in, please sign out first before changing accounts."
        ) from exc
    except AuthenticationFailedError as exc:
        raise click.ClickException(
            "Authentication failed. Please check your username and password and try again."
        ) from exc
    except Authentication2FAFailedError as exc:
        raise click.ClickException(
            "2FA Authentication failed. Please try again."
        ) from exc


@click.command(
    name=SIGNOUT_COMMAND,
    epilog=f"""\b
           Examples:
             {PROGRAM_NAME} {SIGNOUT_COMMAND}
           \b
           To sign in again:
             {PROGRAM_NAME} {SIGNIN_COMMAND}"""
)
@click.pass_context
@run_async
async def signout(ctx):
    """Sign out from Proton VPN and clear local credentials."""
    controller = await Controller.create(params=ctx.obj, click_ctx=ctx)
    was_connected = await controller.is_connection_active()
    await controller.logout()
    completion_message = "You have been successfully signed out."
    if was_connected:
        completion_message = "VPN connection terminated and you've been successfully signed out."

    click.echo(completion_message)


@click.command()
@click.pass_context
@run_async
async def info(ctx):
    """Display your Proton VPN account information."""
    controller = await Controller.create(params=ctx.obj, click_ctx=ctx)
    click.echo(f"Account: '{controller.account_name}'")
