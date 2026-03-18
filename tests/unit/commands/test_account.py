"""
Copyright (c) 2026 Proton AG

Provides CLI command testing for account related functionality.

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
from unittest.mock import AsyncMock, PropertyMock
import pytest

import click
from click.testing import CliRunner

from proton.vpn.cli import app as app_cmd
from proton.vpn.cli.commands.account import SIGNIN_COMMAND, SIGNOUT_COMMAND
from proton.vpn.cli.core.exceptions import \
    Authentication2FAFailedError, \
    AuthenticationFailedError, \
    SignoutRequiredError


def test_signin_fails_when_already_signed_in(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    def login(*_):
        raise SignoutRequiredError

    controller_mock.login.side_effect = login

    result = runner.invoke(
        app_cmd,
        [SIGNIN_COMMAND, "name@email.com"],
        parent=test_context
    )

    assert result.exit_code == 1
    assert "Already signed in, please sign out first before changing accounts."\
        in result.output


def test_signin_fails_when_authentication_fails(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    def login(*_):
        raise AuthenticationFailedError

    controller_mock.login.side_effect = login

    result = runner.invoke(
        app_cmd,
        [SIGNIN_COMMAND, "name@email.com"],
        parent=test_context
    )

    assert result.exit_code == 1
    assert "Authentication failed. Please check your username and password and try again."\
        in result.output


def test_signin_fails_when_2FA_authentication_fails(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    def login(*_):
        raise Authentication2FAFailedError

    controller_mock.login.side_effect = login

    result = runner.invoke(
        app_cmd,
        [SIGNIN_COMMAND, "name@email.com"],
        parent=test_context
    )

    assert result.exit_code == 1
    assert "2FA Authentication failed. Please try again."\
        in result.output


def test_signin_echoes_account_name_on_success(
    controller_mock: AsyncMock,
    cli_invoke
):
    type(controller_mock).account_name = \
        PropertyMock(return_value="testuser@proton.me")

    result = cli_invoke([SIGNIN_COMMAND, "testuser@proton.me"])

    assert result.exit_code == 0
    assert "Successfully signed in as 'testuser@proton.me'" in result.output


def test_signin_echoes_empty_name_when_account_info_missing_name(
    controller_mock: AsyncMock,
    cli_invoke
):
    type(controller_mock).account_name = \
        PropertyMock(return_value=None)

    result = cli_invoke([SIGNIN_COMMAND, "testuser@proton.me"])

    assert result.exit_code == 0
    assert "Successfully signed in as 'None'" in result.output


def test_signout_echoes_signed_out_message_when_not_connected(
    controller_mock: AsyncMock,
    cli_invoke
):
    controller_mock.is_connection_active.return_value = False

    result = cli_invoke([SIGNOUT_COMMAND])

    assert result.exit_code == 0
    assert "You have been successfully signed out." in result.output


def test_signout_echoes_connection_terminated_message_when_connected(
    controller_mock: AsyncMock,
    cli_invoke
):
    controller_mock.is_connection_active.return_value = True

    result = cli_invoke([SIGNOUT_COMMAND])

    assert result.exit_code == 0
    assert "VPN connection terminated and you've been successfully signed out." in result.output
