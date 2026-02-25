"""
Copyright (c) 2026 Proton AG

Provides CLI command testing for server command help content.

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
from proton.vpn.cli.commands.server import \
    CONNECT_COMMAND, \
    DISCONNECT_COMMAND, \
    SERVER_NAME_ARGUMENT


def test_connect_help_explains_server_name_argument(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CONNECT_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Arguments:" in result.output
    assert SERVER_NAME_ARGUMENT in result.output
    assert "Connect to specific server by ID (e.g., IT#23)" in result.output


def test_connect_help_shows_examples_section(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CONNECT_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Examples:" in result.output


def test_connect_help_shows_quick_connection_example(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CONNECT_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "# Quick connection" in result.output
    assert "# Fastest server globally" in result.output


def test_connect_help_shows_location_selection_examples(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CONNECT_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "# Location selection" in result.output
    assert "--country US" in result.output
    assert "--city \"New York\"" in result.output


def test_connect_help_shows_feature_flag_examples(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CONNECT_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "# Feature-based selection" in result.output
    assert "--p2p" in result.output


def test_connect_help_shows_extra_secure_connection_examples(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CONNECT_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "# Extra secure connections" in result.output
    assert "--securecore" in result.output
    assert "--tor" in result.output


def test_connect_help_describes_country_option(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CONNECT_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Options:" in result.output
    assert "Connect to fastest server in specified country" in result.output
    assert "Country code (US, GB, DE) or full name" in result.output


def test_connect_help_describes_city_option(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CONNECT_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Connect to fastest server in specified city" in result.output
    assert "City name (use quotes for multi-word: \"New York\")" in result.output


def test_connect_help_describes_p2p_option(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CONNECT_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Connect to fastest P2P-optimized server" in result.output


def test_connect_help_describes_securecore_option(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CONNECT_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Connect to fastest Secure Core server" in result.output


def test_connect_help_describes_tor_option(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CONNECT_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Connect to fastest Tor server" in result.output


def test_connect_help_describes_random_option(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CONNECT_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Connect to random available server" in result.output


def test_disconnect_help_shows_examples_section(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [DISCONNECT_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Examples:" in result.output
