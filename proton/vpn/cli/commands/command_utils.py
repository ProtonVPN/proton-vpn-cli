"""
Utilities to facilitate command implementation.

Copyright (c) 2026 Proton AG

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

from proton.vpn.cli.core.controller import Controller


async def inform_that_expired_serverlist_will_be_updated_if_necessary(controller: Controller):
    """Warns user of server list update if it has expired"""
    if await controller.is_serverlist_expired():
        click.echo("Server list is outdated, updating... This may take a moment.")
