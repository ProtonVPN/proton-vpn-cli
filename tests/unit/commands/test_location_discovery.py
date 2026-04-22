"""
Copyright (c) 2026 Proton AG

Provides CLI command testing for server location discovery.

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
import pytest

import click
from click.testing import CliRunner

from proton.vpn.cli import app as app_cmd
from proton.vpn.cli.commands.account import SIGNIN_COMMAND
from proton.vpn.cli.commands.location_discovery import \
    COUNTRIES_COMMAND, \
    COUNTRIES_LIST_COMMAND, \
    CITIES_COMMAND, \
    CITIES_LIST_COMMAND, \
    FEATURES_TO_DISPLAY
from proton.vpn.cli.core.exceptions import \
    AuthenticationRequiredError, \
    CountryCodeError, \
    CountryNameError
from proton.vpn.session.dataclasses.servers import Country
from proton.vpn.session.servers.types import ServerFeatureEnum
from proton.vpn.session.servers.logicals import LogicalServer


@pytest.mark.parametrize("server_list_expired", [True, False])
def test_countries_listing_notifies_of_serverlist_update_when_expired(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock,
    server_list_expired: bool,
):
    controller_mock.is_serverlist_expired.return_value = server_list_expired

    result = runner.invoke(
        app_cmd,
        [COUNTRIES_COMMAND, COUNTRIES_LIST_COMMAND],
        parent=test_context
    )

    assert ("Server list is outdated, updating... This may take a moment."
            in result.output) == server_list_expired


def test_countries_listing_fails_when_not_signed_in(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    def get_all_countries(*_):
        raise AuthenticationRequiredError

    controller_mock.get_all_countries.side_effect = get_all_countries

    result = runner.invoke(
        app_cmd,
        [COUNTRIES_COMMAND, COUNTRIES_LIST_COMMAND],
        parent=test_context
    )

    assert result.exit_code == 2
    assert "Authentication required to view complete country list. " \
            f"Please sign in with '{test_context.info_name} {SIGNIN_COMMAND}'" \
            in result.output


def test_countries_listing_shows_available_countries(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    def get_all_countries(*_):
        return [
            Country("UK", []),
            Country("PL", []),
            Country("FR", []),
            Country("CH", [])
        ]

    controller_mock.get_all_countries.side_effect = get_all_countries

    result = runner.invoke(
        app_cmd,
        [COUNTRIES_COMMAND, COUNTRIES_LIST_COMMAND],
        parent=test_context
    )

    assert result.exit_code == 0

    for country in get_all_countries():
        assert country.code in result.output
        assert country.name in result.output

    header_newline_count = 2
    row_count = result.output.count("\n") - header_newline_count - 1
    assert row_count == len(get_all_countries())


@pytest.mark.parametrize("server_list_expired", [True, False])
def test_cities_listing_notifies_of_serverlist_update_when_expired(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock,
    server_list_expired: bool
):
    controller_mock.is_serverlist_expired.return_value = server_list_expired

    result = runner.invoke(
        app_cmd,
        [CITIES_COMMAND, CITIES_LIST_COMMAND, "COUNTRY_CODE"],
        parent=test_context
    )

    assert ("Server list is outdated, updating... This may take a moment."
            in result.output) == server_list_expired


def test_cities_listing_listing_fails_when_not_signed_in(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    def get_all_countries(*_):
        raise AuthenticationRequiredError

    controller_mock.get_all_countries.side_effect = get_all_countries

    result = runner.invoke(
        app_cmd,
        [CITIES_COMMAND, CITIES_LIST_COMMAND, "COUNTRY_CODE"],
        parent=test_context
    )

    assert result.exit_code == 2
    assert "Authentication required to view cities. " \
           f"Please sign in with '{test_context.info_name} {SIGNIN_COMMAND}'" \
           in result.output


def test_cities_listing_fails_when_provided_invalid_country_code(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    def validate_country_input(*_):
        raise CountryCodeError

    controller_mock.validate_country_input.side_effect = validate_country_input

    result = runner.invoke(
        app_cmd,
        [CITIES_COMMAND, CITIES_LIST_COMMAND, "COUNTRY_CODE"],
        parent=test_context
    )

    assert result.exit_code == 2
    assert "Invalid country code 'COUNTRY_CODE'. Please use a valid country code."\
        in result.output


def test_cities_listing_fails_when_provided_invalid_country_name(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    def validate_country_input(*_):
        raise CountryNameError

    controller_mock.validate_country_input.side_effect = validate_country_input

    result = runner.invoke(
        app_cmd,
        [CITIES_COMMAND, CITIES_LIST_COMMAND, "COUNTRY_NAME"],
        parent=test_context
    )

    assert result.exit_code == 2
    assert "Invalid country name 'COUNTRY_NAME'. Please use a valid country name."\
        in result.output
    

def test_cities_listing_fails_when_country_not_found(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CITIES_COMMAND, CITIES_LIST_COMMAND, "COUNTRY_NAME"],
        parent=test_context
    )

    assert result.exit_code == 2
    assert f"Country 'COUNTRY_NAME' not found. " \
           f"Use '{test_context.info_name} {COUNTRIES_COMMAND}' to see available options." \
           in result.output


def test_cities_listing_shows_all_available_features_for_city(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    def get_all_countries(*_):
        return [
            Country(
                code="uk",
                servers=[
                    LogicalServer({
                        "Features": ServerFeatureEnum.P2P,
                        "City": "London",
                        "Tier": "1",
                        "Enabled": "1"
                    }),
                    LogicalServer({
                        "Features": ServerFeatureEnum.SECURE_CORE,
                        "City": "London",
                        "Tier": "1",
                        "Enabled": "1"
                    }),
                    LogicalServer({
                        "Features": ServerFeatureEnum.STREAMING,
                        "City": "London",
                        "Tier": "1",
                        "Enabled": "1"
                    })
                ],
            )
        ]

    def validate_country_input(*_):
        return get_all_countries()[0].code

    controller_mock.get_all_countries.side_effect = get_all_countries
    controller_mock.validate_country_input.side_effect = validate_country_input

    result = runner.invoke(
        app_cmd,
        [CITIES_COMMAND, CITIES_LIST_COMMAND, "UK"],
        parent=test_context
    )

    assert result.exit_code == 0

    only_country = get_all_countries()[0]
    only_city = only_country.cities[0]
    for feature in only_city.features:
        if feature in FEATURES_TO_DISPLAY:
            assert FEATURES_TO_DISPLAY[feature] in result.output

    assert only_city.name in result.output


def test_cities_listing_shows_all_available_cities(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    def get_all_countries(*_):
        return [
            Country(
                code="uk",
                servers=[
                    LogicalServer({
                        "Features": ServerFeatureEnum.P2P,
                        "City": "London",
                        "Tier": "1",
                        "Enabled": "1"
                    }),
                    LogicalServer({
                        "Features": ServerFeatureEnum.SECURE_CORE,
                        "City": "Manchester",
                        "Tier": "1",
                        "Enabled": "1"
                    }),
                    LogicalServer({
                        "Features": ServerFeatureEnum.STREAMING,
                        "City": "Cardiff",
                        "Tier": "1",
                        "Enabled": "1"
                    })
                ],
            )
        ]

    def validate_country_input(*_):
        return get_all_countries()[0].code

    controller_mock.get_all_countries.side_effect = get_all_countries
    controller_mock.validate_country_input.side_effect = validate_country_input

    result = runner.invoke(
        app_cmd,
        [CITIES_COMMAND, CITIES_LIST_COMMAND, "UK"],
        parent=test_context
    )

    assert result.exit_code == 0

    only_country = get_all_countries()[0]
    for city in only_country.cities:
        assert city.name in result.output

    result_without_header = result.output.split("-\n", 1)[1]
    number_of_city_rows = result_without_header.count("\n") - 1
    assert number_of_city_rows == len(only_country.cities)
