"""
Copyright (c) 2026 Proton AG

Provides CLI command testing for main app help content.

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
from proton.vpn.cli.commands.account import SIGNIN_COMMAND
from proton.vpn.cli.commands.server import CONNECT_COMMAND, DISCONNECT_COMMAND
from proton.vpn.cli.commands.settings import SETTINGS_LIST_COMMAND


def test_app_help_shows_examples_section(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Examples:" in result.output


def test_app_help_examples_include_key_commands(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert SIGNIN_COMMAND in result.output
    assert CONNECT_COMMAND in result.output
    assert DISCONNECT_COMMAND in result.output
    assert SETTINGS_LIST_COMMAND in result.output


def test_app_help_examples_include_country_flag(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "--country" in result.output


def test_app_help_shows_quick_start_section(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Quick Start:" in result.output
    assert "Sign in" in result.output
    assert "Connect" in result.output
    assert "Disconnect" in result.output


def test_app_help_shows_get_command_help_guidance(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Get Command Help:" in result.output
    assert HELP_OPTION in result.output


def test_app_help_shows_documentation_url(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Documentation:" in result.output
    assert "https://protonvpn.com/support/cli-guide" in result.output


def test_app_help_shows_support_links(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Support:" in result.output
    assert "https://protonvpn.com/support-form" in result.output
    assert "support@protonvpn.com" in result.output
