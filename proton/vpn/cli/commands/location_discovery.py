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
import click
from tabulate import tabulate

from proton.vpn.cli._program_name import PROGRAM_NAME
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
from proton.vpn.cli.commands.server import CONNECT_COMMAND

COUNTRIES_COMMAND = "countries"
COUNTRIES_LIST_COMMAND = "list"
CITIES_COMMAND = "cities"
CITIES_LIST_COMMAND = "list"
COUNTRY_ARGUMENT = "COUNTRY"

FEATURES_TO_DISPLAY = {
    ServerFeatureEnum.P2P: "P2P",
    ServerFeatureEnum.SECURE_CORE: "Secure Core",
    ServerFeatureEnum.TOR: "Tor",
}


def _print_usage_error(msg: str):
    raise click.UsageError(msg)


@click.group(
    name=COUNTRIES_COMMAND,
    epilog=f"""\b
Output:
  Displays country names with their two-letter codes and server counts.
\b
Examples:
  {PROGRAM_NAME} {COUNTRIES_COMMAND} {COUNTRIES_LIST_COMMAND}
\b
Connect to a country:
  {PROGRAM_NAME} {CONNECT_COMMAND} --country <CODE>
\b
Explore cities in a country:
  {PROGRAM_NAME} {CITIES_COMMAND} {CITIES_LIST_COMMAND} <COUNTRY>"""
)
@run_async
async def countries():
    """Discover all countries where Proton VPN servers are available."""


@countries.command(
    name=COUNTRIES_LIST_COMMAND,
    short_help="List all countries where Proton VPN servers are available."
)
@click.pass_context
@run_async
async def list_countries(ctx):
    """List all countries where Proton VPN servers are available."""
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


@click.group(
    name=CITIES_COMMAND,
    short_help="Discover cities where servers are available in a specific country.",
    epilog=f"""
\b
Country Format:
  Two-letter code: US, GB, DE
  Full name: "United States", "Germany" (use quotes for multi-word)
\b
Examples:
  {PROGRAM_NAME} {CITIES_COMMAND} {CITIES_LIST_COMMAND} US               # Cities in US (direct argument)
  {PROGRAM_NAME} {CITIES_COMMAND} {CITIES_LIST_COMMAND} "United States"  # Full country name
\b
Connect to a city:
  {PROGRAM_NAME} {CONNECT_COMMAND} --city <CITY>
\b
To see available countries:
  {PROGRAM_NAME} {COUNTRIES_COMMAND} {COUNTRIES_LIST_COMMAND}"""  # noqa:E501
)
@run_async
async def cities():
    """Discover cities where servers are available in a specific country."""


@cities.command(
    name=CITIES_LIST_COMMAND,
    short_help="Shows a list of cities where servers are available in a specific country."
)
@click.argument(COUNTRY_ARGUMENT, required=True)
@click.pass_context
@run_async
async def list_cities_in_country(ctx, country: str):
    """
    Shows a list of cities where servers are available in a specific country.

    Arguments:

    COUNTRY    Country code (US, GB, DE) or full name ("United States")
    """
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
        country_code = controller.validate_country_input(country)
    except CountryCodeError:
        _print_usage_error(
            f"Invalid country code '{country}'. Please use a valid country code."
        )
    except CountryNameError:
        _print_usage_error(
            f"Invalid country name '{country}'. Please use a valid country name."
        )

    requested_country = \
        list(filter(lambda country: country.code == country_code.lower(), all_countries))

    if not requested_country:
        _print_usage_error(
            f"Country '{country}' not found. "
            f"Use '{controller.program_name} {COUNTRIES_COMMAND}' to see available options."
        )

    requested_country = requested_country.pop()
    table_data = []

    for city in requested_country.cities:
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

    click.echo(f"\nCities in {requested_country.name}:\n{table}\n")
