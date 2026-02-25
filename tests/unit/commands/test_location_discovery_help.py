"""
Copyright (c) 2026 Proton AG

Provides CLI command testing for location discovery command help content.

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
from proton.vpn.cli.commands.location_discovery import \
    COUNTRIES_COMMAND, \
    COUNTRIES_LIST_COMMAND, \
    CITIES_COMMAND, \
    CITIES_LIST_COMMAND, \
    COUNTRY_ARGUMENT
from proton.vpn.cli.commands.server import CONNECT_COMMAND


def test_countries_help_shows_output_description(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [COUNTRIES_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Output:" in result.output


def test_countries_help_shows_examples_section(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [COUNTRIES_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Examples:" in result.output
    assert COUNTRIES_LIST_COMMAND in result.output


def test_countries_help_shows_connect_country_guidance(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [COUNTRIES_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Connect to a country:" in result.output
    assert CONNECT_COMMAND in result.output
    assert "--country" in result.output


def test_countries_help_shows_cities_cross_reference(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [COUNTRIES_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Explore cities in a country:" in result.output
    assert CITIES_COMMAND in result.output
    assert CITIES_LIST_COMMAND in result.output


def test_countries_help_describes_subcommand(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [COUNTRIES_COMMAND, COUNTRIES_LIST_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "List all countries where Proton VPN servers are available." \
        in result.output


def test_cities_help_shows_country_format_guidance(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CITIES_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Country Format:" in result.output
    assert "US, GB, DE" in result.output  # country code examples
    assert "\"United States\"" in result.output  # multi word country example


def test_cities_help_shows_examples_section(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CITIES_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Examples:" in result.output
    assert CITIES_LIST_COMMAND in result.output


def test_cities_help_shows_connect_city_guidance(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CITIES_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Connect to a city:" in result.output
    assert CONNECT_COMMAND in result.output
    assert "--city" in result.output


def test_cities_help_shows_countries_cross_reference(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CITIES_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "To see available countries:" in result.output
    assert COUNTRIES_COMMAND in result.output


def test_cities_help_describes_subcommand(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CITIES_COMMAND, CITIES_LIST_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Shows a list of cities where servers are available in a specific country." \
        in result.output


def test_cities_list_help_explains_argument(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CITIES_COMMAND, CITIES_LIST_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Arguments:" in result.output
    assert COUNTRY_ARGUMENT in result.output
    assert "Country code (US, GB, DE) or full name (\"United States\")" \
        in result.output
