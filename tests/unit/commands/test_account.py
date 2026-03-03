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
from proton.vpn.cli.commands.account import SIGNIN_COMMAND
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
