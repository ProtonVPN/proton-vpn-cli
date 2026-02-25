"""
Copyright (c) 2026 Proton AG

Provides CLI command testing for account command help content.

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
from unittest.mock import AsyncMock

import click
from click.testing import CliRunner

from proton.vpn.cli import app as app_cmd, HELP_OPTION
from proton.vpn.cli.commands.account import SIGNIN_COMMAND, SIGNOUT_COMMAND


def test_signin_help_shows_examples_section(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [SIGNIN_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Examples:" in result.output


def test_signin_help_shows_example_with_email(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [SIGNIN_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "user@proton.me" in result.output


def test_signout_help_shows_examples_section(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [SIGNOUT_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Examples:" in result.output


def test_signout_help_shows_signin_guidance(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [SIGNOUT_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "To sign in again:" in result.output
    assert SIGNIN_COMMAND in result.output
