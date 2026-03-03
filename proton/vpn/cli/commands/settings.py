"""
Set features commands.

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
from __future__ import annotations
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol

import click
from tabulate import tabulate

from proton.vpn.killswitch.interface import KillSwitchState
from proton.vpn.core.settings.features import NetShield
from proton.vpn.core.settings.custom_dns import CustomDNS
from proton.vpn.cli.core.run_async import run_async
from proton.vpn.cli.core.controller import Controller, Feature
from proton.vpn.cli.core.exceptions import AuthenticationRequiredError, \
    RequiresHigherTierError, InvalidDNS
from proton.vpn.cli.commands.account import SIGNIN_COMMAND, SIGNOUT_COMMAND


class ClickArgType(Protocol):
    """Maps between VPN state types and click friendly formats"""

    @staticmethod
    @abstractmethod
    def get_human_friendly_state_string(value: Any) -> str:
        """Returns human friendly state string for the specified value."""
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def to_list_of_str() -> list[str]:
        """Converts to a list of all possible click value strings

        This is a necessary change because <8.2.0, `click.Choice`
        can only take a list of strings. With version >=8.2.0 click
        supports non-string choices (you can pass an enum class).
        This change is to make it backwards compatible, as on Fedora 43
        click is v8.1.7 and on Ubuntu 24.04 v8.1.6.
        See more here: https://click.palletsprojects.com/en/stable/api/#click.Choice
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def from_str(value: str) -> Any:
        """Returns value based on provided click string"""
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def to_str(value: Any) -> str:
        """Returns click string based on provided value"""
        raise NotImplementedError


class ToggleType(ClickArgType):
    """Represents simple binary options that a user can select."""

    @staticmethod
    def get_human_friendly_state_string(value: bool) -> str:
        """Returns human friendly state string for the specified value."""
        if value is False:
            return "disabled"

        return "enabled"

    @staticmethod
    def to_list_of_str() -> list[str]:
        """Converts to a list of all possible click value strings"""
        return ["off", "on"]

    @staticmethod
    def from_str(value: str) -> bool:
        """Returns value based on provided click string"""
        if value.lower() == "off":
            return False

        return True

    @staticmethod
    def to_str(value: bool) -> str:
        """Returns click string based on provided value"""
        if value is False:
            return "off"

        return "on"


class CustomDNSType(ToggleType):
    """Toggle extension for CustomDNS"""

    @staticmethod
    def to_str(value: CustomDNS) -> str:
        """Returns click string based on provided value"""
        enabled = ToggleType.to_str(value.enabled)

        max_ip_list_length = 2
        if value.ip_list:
            ips = value.ip_list[:max_ip_list_length]
            ips_to_show = [str(dns.ip) for dns in ips]
            if len(value.ip_list) > max_ip_list_length:
                ips_to_show.append("...")
            return f"{enabled}  [{', '.join(ips_to_show)}]"

        # no DNS IPs to show
        return enabled


class KillSwitchType(ClickArgType):
    """Represents the various kill switch states that a user can select"""
    # Advanced option is temporarily removed as
    # currently it's not possible to establish a connection with it enabled,
    # while being disconnected.

    @staticmethod
    def get_human_friendly_state_string(value: KillSwitchState) -> str:
        """Returns human friendly state string for the specified value."""
        if value == KillSwitchState.OFF:
            return "disabled"

        return "standard"

    @staticmethod
    def to_list_of_str() -> list[str]:
        """Converts to a list of all possible click value strings

        See explanation above.
        """
        return ["off", "standard"]

    @staticmethod
    def from_str(value: str) -> KillSwitchState:
        """Returns value based on provided click string"""
        if value.upper() == KillSwitchState.OFF.name:
            return KillSwitchState.OFF

        return KillSwitchState.ON

    @staticmethod
    def to_str(value: KillSwitchState) -> str:
        """Returns click string based on provided value"""
        if value == KillSwitchState.OFF:
            return "off"

        return "standard"


class NetshieldType(ClickArgType):
    """Represent the various netshield states that a user can select"""
    @staticmethod
    def get_human_friendly_state_string(value: NetShield) -> str:
        """Returns human friendly state string for the specified value."""
        if value == NetShield.NO_BLOCK:
            return "disabled"

        if value == NetShield.BLOCK_MALICIOUS_URL:
            return "malware only"

        return "malware, ads and trackers"

    @staticmethod
    def to_list_of_str() -> list[str]:
        """Converts to a list of all possible click value strings"""
        return ["off", "malware-only", "malware-ads-trackers"]

    @staticmethod
    def from_str(value: str) -> NetShield:
        """Returns value based on provided click string"""
        if value == "off":
            return NetShield.NO_BLOCK

        if value == "malware-only":
            return NetShield.BLOCK_MALICIOUS_URL

        return NetShield.BLOCK_ADS_AND_TRACKING

    @staticmethod
    def to_str(value: NetShield) -> str:
        """Returns click string based on provided value"""
        if value == NetShield.NO_BLOCK:
            return "off"

        if value == NetShield.BLOCK_MALICIOUS_URL:
            return "malware-only"

        return "malware-ads-trackers"


@dataclass
class ClickFeature(Feature):
    """Click specific feature data"""
    command: str = None
    human_friendly_name: str = None
    short_help: str = None
    click_type: ClickArgType = None


REQUIRES_SUBSCRIPTION_PLAN = ". Requires subscription plan"

BOOL_FEATURES = [
    ClickFeature(
        command="vpn-accelerator",
        human_friendly_name="VPN Accelerator",
        setting_path="features.vpn_accelerator",
        short_help=f"Toggle VPN Accelerator{REQUIRES_SUBSCRIPTION_PLAN}",
        click_type=ToggleType()
    ),
    ClickFeature(
        command="moderate-nat",
        human_friendly_name="Moderate NAT",
        setting_path="features.moderate_nat",
        short_help=f"Toggle Moderate NAT{REQUIRES_SUBSCRIPTION_PLAN}",
        click_type=ToggleType()
    ),
    ClickFeature(
        command="ipv6",
        human_friendly_name="IPv6",
        setting_path="ipv6",
        short_help="Toggle IPv6",
        available_on_free_tier=True,
        requires_restart=True,
        click_type=ToggleType()
    ),
    ClickFeature(
        command="anonymous-crash-reports",
        human_friendly_name="Anonymous crash reports",
        setting_path="anonymous_crash_reports",
        short_help="Toggle anonymous crash reports",
        available_on_free_tier=True,
        click_type=ToggleType()
    ),
    ClickFeature(
        command="port-forwarding",
        human_friendly_name="Port forwarding",
        setting_path="features.port_forwarding",
        short_help=f"Toggle Port forwarding{REQUIRES_SUBSCRIPTION_PLAN}",
        click_type=ToggleType()
    )
]
CUSTOM_DNS_FEATURE = ClickFeature(
    command="custom-dns",
    human_friendly_name="Custom DNS",
    setting_path="custom_dns",
    short_help=f"Toggle Custom DNS and set DNS servers{REQUIRES_SUBSCRIPTION_PLAN}",
    requires_restart=True,
    click_type=CustomDNSType()
)
NETSHIELD_FEATURE = ClickFeature(
    command="netshield",
    human_friendly_name="NetShield",
    setting_path="features.netshield",
    short_help=f"Set NetShield mode{REQUIRES_SUBSCRIPTION_PLAN}",
    click_type=NetshieldType()
)
KILLSWITCH_FEATURE = ClickFeature(
    command="kill-switch",
    human_friendly_name="Kill switch",
    setting_path="killswitch",
    available_on_free_tier=True,
    click_type=KillSwitchType()
)


def _raise_error_auth_required(controller: Controller, action: str) -> None:
    raise click.UsageError(
        f"Authentication required to {action} feature status. "
        f"Please sign in with '{controller.program_name} {SIGNIN_COMMAND}'"
    )


def _raise_error_requires_higher_tier(feature_human_friendly_name: str) -> None:
    raise click.UsageError(
        f"{feature_human_friendly_name} feature is not available "
        "on your current subscription plan. "
        "Please upgrade to access this feature."
    )


def _print_success_message(
    feature: Feature,
    mode: str,
    is_connection_active: bool = False
) -> None:
    msg = f"{feature.human_friendly_name} has been set to {mode}"

    if feature.requires_restart and is_connection_active:
        msg += ", please establish a new VPN connection for " \
            "changes to take effect."

    click.echo(msg)


@click.group()
def config():
    """Configure Proton VPN settings"""


CONFIG_COMMAND = config.name
SET_COMMAND = "set"


@config.group(name=SET_COMMAND)
def set_group():
    """Change a specific setting"""


def _register_bool_feature_command(group: click.Group, feature: Feature):
    @group.command(name=feature.command, help=feature.short_help)
    @click.argument("state", type=click.Choice(ToggleType.to_list_of_str(), case_sensitive=False))
    @click.pass_context
    @run_async
    async def _bool_command(ctx: click.Context, state: str) -> None:
        controller = await Controller.create(params=ctx.obj, click_ctx=ctx)
        toggle_value = ToggleType.from_str(state)
        try:
            await controller.save_feature_setting(feature, toggle_value)
        except AuthenticationRequiredError:
            _raise_error_auth_required(controller, action="set")
        except RequiresHigherTierError:
            _raise_error_requires_higher_tier(feature.human_friendly_name)
        else:
            _print_success_message(
                feature,
                ToggleType.get_human_friendly_state_string(toggle_value),
                is_connection_active=await controller.is_connection_active()
            )


for _feature in BOOL_FEATURES:
    _register_bool_feature_command(set_group, _feature)


@set_group.command(name=KILLSWITCH_FEATURE.command, help=KILLSWITCH_FEATURE.short_help)
@click.argument("mode", type=click.Choice(KillSwitchType.to_list_of_str(), case_sensitive=False))
@click.pass_context
@run_async
async def killswitch_command(ctx: click.Context, mode: str) -> None:
    """Set Kill Switch mode"""
    controller = await Controller.create(params=ctx.obj, click_ctx=ctx)
    killswitch_value = KillSwitchType.from_str(mode)

    try:
        await controller.save_feature_setting(KILLSWITCH_FEATURE, killswitch_value)
    except AuthenticationRequiredError:
        _raise_error_auth_required(controller, action="set")
    else:
        _print_success_message(
            KILLSWITCH_FEATURE,
            KillSwitchType.get_human_friendly_state_string(killswitch_value)
        )


@set_group.command(name=NETSHIELD_FEATURE.command, help=NETSHIELD_FEATURE.short_help)
@click.argument(
    "mode",
    type=click.Choice(NetshieldType.to_list_of_str(), case_sensitive=False),
)
@click.pass_context
@run_async
async def netshield_command(ctx: click.Context, mode: str) -> None:
    """Set NetShield mode"""
    controller = await Controller.create(params=ctx.obj, click_ctx=ctx)
    netshield_value = NetshieldType.from_str(mode)

    try:
        await controller.save_feature_setting(NETSHIELD_FEATURE, netshield_value)
    except AuthenticationRequiredError:
        _raise_error_auth_required(controller, action="set")
    except RequiresHigherTierError:
        _raise_error_requires_higher_tier(NETSHIELD_FEATURE.human_friendly_name)
    else:
        _print_success_message(
            NETSHIELD_FEATURE,
            f"'{NetshieldType.get_human_friendly_state_string(netshield_value)}'"
        )


@set_group.command(name=CUSTOM_DNS_FEATURE.command, help=CUSTOM_DNS_FEATURE.short_help)
@click.argument("state", type=click.Choice(ToggleType.to_list_of_str(), case_sensitive=False))
@click.option("--dns", "dns_csv", help="Comma-separated DNS servers, e.g. 1.1.1.1,9.9.9.9")
@click.pass_context
@run_async
async def custom_dns_command(ctx: click.Context, state: str, dns_csv: str | None) -> None:
    """Toggle Custom DNS and set DNS servers"""
    controller = await Controller.create(params=ctx.obj, click_ctx=ctx)
    toggle_value = ToggleType.from_str(state)

    parsed_dns_ips = []
    dns_list = [x.strip() for x in dns_csv.split(",") if x.strip()] if dns_csv else []

    if toggle_value is True:
        if not dns_list:
            raise click.UsageError(
                f"When enabling {CUSTOM_DNS_FEATURE.human_friendly_name} feature "
                "you must provide a list of comma separated DNS's."
            )

        try:
            parsed_dns_ips = controller.parse_dns_ips(dns_list)
        except InvalidDNS as excp:
            raise click.UsageError(
                f"Invalid DNS address '{excp.dns}'. Please provide a valid IPv4 address."
            )

    custom_dns = controller.to_custom_dns(toggle_value, parsed_dns_ips)

    try:
        await controller.save_feature_setting(CUSTOM_DNS_FEATURE, custom_dns)
    except AuthenticationRequiredError:
        _raise_error_auth_required(controller, action="set")
    except RequiresHigherTierError:
        _raise_error_requires_higher_tier(CUSTOM_DNS_FEATURE.human_friendly_name)
    else:
        _print_success_message(
            CUSTOM_DNS_FEATURE,
            ToggleType.get_human_friendly_state_string(toggle_value),
            is_connection_active=await controller.is_connection_active()
        )


SETTINGS_LIST_COMMAND = "list"


@config.command(name=SETTINGS_LIST_COMMAND)
@click.pass_context
@run_async
async def list_features(ctx: click.Context):
    """Show current configuration for all settings"""
    controller = await Controller.create(params=ctx.obj, click_ctx=ctx)

    all_features = BOOL_FEATURES.copy()
    all_features.extend([CUSTOM_DNS_FEATURE, KILLSWITCH_FEATURE, NETSHIELD_FEATURE])
    settings_table = []
    for feature in all_features:
        try:
            setting = await controller.get_feature_setting(feature)
        except AuthenticationRequiredError:
            _raise_error_auth_required(controller, action="view")

        feature_requires_upgrade =\
            not feature.available_on_free_tier and controller.user_on_free_tier

        setting_str = \
            "Upgrade to enable" if feature_requires_upgrade\
            else feature.click_type.to_str(setting)
        settings_table.append((feature.command, setting_str))

    table = tabulate(
        settings_table,
        headers=["Setting", "Value"],
        tablefmt="simple",
        stralign="left",
        numalign="right",
    )
    click.echo(f"\nCurrent configuration\n{table}\n")

    # determine footer guidance
    if controller.user_on_free_tier:
        program_name = controller.program_name
        click.echo(
            "To upgrade to VPN Plus visit: https://account.protonvpn.com/pricing\n"
            "After upgrading online:\n"
            "    Sign out and sign in again to activate your new plan:\n"
            f"    {program_name} {SIGNOUT_COMMAND} && {program_name} {SIGNIN_COMMAND}"
        )
    else:
        full_set_command_str = f"{controller.program_name} {config.name} {set_group.name}"
        help_option_str = ctx.help_option_names[0]
        click.echo(
            f"Use '{full_set_command_str} <setting> <value>' to change settings.\n"
            f"Use '{full_set_command_str} <setting> {help_option_str}' for available values."
        )
