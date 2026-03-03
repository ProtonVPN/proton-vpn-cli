"""
Server/Connection related commands.

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
import sys
import os

import click
from tabulate import tabulate

from proton.vpn.cli.core.run_async import run_async
from proton.vpn.cli.core.controller import Controller
from proton.vpn.session.servers.types import ServerFeatureEnum
from proton.vpn.cli.core.exceptions import \
    AuthenticationRequiredError, \
    CountryCodeError, \
    CountryNameError
from proton.vpn.cli.commands.account import SIGNIN_COMMAND
from proton.vpn.cli.commands.command_utils import \
    inform_that_expired_serverlist_will_be_updated_if_necessary


FEATURES_TO_DISPLAY = {
    ServerFeatureEnum.P2P: "P2P",
    ServerFeatureEnum.SECURE_CORE: "Secure Core",
    ServerFeatureEnum.TOR: "Tor",
}


def _print_usage_error(msg: str):
    raise click.UsageError(msg)


@click.group()
@run_async
async def countries():
    """Discover available countries"""


COUNTRIES_COMMAND = countries.name
COUNTRIES_LIST_COMMAND = "list"


@countries.command(name=COUNTRIES_LIST_COMMAND)
@click.pass_context
@run_async
async def list_countries(ctx):
    """Display all available countries."""
    controller = await Controller.create(params=ctx.obj, click_ctx=ctx)

    await inform_that_expired_serverlist_will_be_updated_if_necessary(controller)

    try:
        all_countries = await controller.get_all_countries()
    except AuthenticationRequiredError:
        _print_usage_error(
            "Authentication required to view complete country list. "
            f"Please sign in with '{controller.program_name} {SIGNIN_COMMAND}'"
        )
        return

    table = tabulate(
        [(country.name, country.code.upper()) for country in all_countries],
        headers=["Country", "Code"],
        tablefmt="simple",
        stralign="left",
        numalign="right",
    )
    click.echo(table)


@click.group()
@run_async
async def cities():
    """Discover available cities"""


CITIES_COMMAND = cities.name
CITIES_LIST_COMMAND = "list"
PROGRAM_NAME = os.path.basename(sys.argv[0])


@cities.command(
    name=CITIES_LIST_COMMAND,
    epilog=f"""\b
    Examples:
        {PROGRAM_NAME} {cities.name} {CITIES_LIST_COMMAND} PT     Display cities in Portugal
        {PROGRAM_NAME} {cities.name} {CITIES_LIST_COMMAND} US     Display cities in United States"""
)
@click.argument("country_input", required=True)
@click.pass_context
@run_async
async def list_cities_in_country(ctx, country_input: str):
    """Display cities within a country"""
    controller = await Controller.create(params=ctx.obj, click_ctx=ctx)

    await inform_that_expired_serverlist_will_be_updated_if_necessary(controller)

    try:
        all_countries = await controller.get_all_countries()
    except AuthenticationRequiredError:
        _print_usage_error(
            "Authentication required to view cities. "
            f"Please sign in with '{controller.program_name} {SIGNIN_COMMAND}'"
        )

    try:
        country_code = controller.validate_country_input(country_input)
    except CountryCodeError:
        _print_usage_error(
            f"Invalid country code '{country_input}'. Please use a valid country code."
        )
    except CountryNameError:
        _print_usage_error(
            f"Invalid country name '{country_input}'. Please use a valid country name."
        )

    country = list(filter(lambda country: country.code == country_code.lower(), all_countries))

    if not country:
        _print_usage_error(
            f"Country '{country_input}' not found. "
            f"Use '{controller.program_name} {COUNTRIES_COMMAND}' to see available options."
        )

    country = country.pop()
    table_data = []

    for city in country.cities:
        only_displayable_features = [
            feature_display_name
            for feature, feature_display_name in FEATURES_TO_DISPLAY.items()
            if feature in city.features
        ]
        sorted_human_readable_features = sorted(only_displayable_features)

        table_data.append((city.name, ", ".join(sorted_human_readable_features)))

    table = tabulate(
        table_data,
        headers=["City", "Features"],
        tablefmt="simple",
        stralign="left",
        numalign="right",
    )

    click.echo(f"\nCities in {country.name}:\n{table}\n")
