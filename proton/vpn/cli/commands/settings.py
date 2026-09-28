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
import click
from tabulate import tabulate

from proton.vpn.cli._cli_constants import PROGRAM_NAME
from proton.vpn.cli.core.run_async import run_async
from proton.vpn.cli.core.controller import Controller
from proton.vpn.cli.core.exceptions import \
    AuthenticationRequiredError, \
    RequiresHigherTierError, \
    InvalidDNS
from proton.vpn.cli.commands.account import SIGNIN_COMMAND, SIGNOUT_COMMAND
from proton.vpn.cli.commands.feature_setting_definitions import \
    ALL_FEATURES, \
    BOOL_FEATURES, \
    ClickFeature, \
    ToggleType, \
    KillSwitchType, \
    NetshieldType, \
    ProtocolType, \
    CUSTOM_DNS_FEATURE, \
    IPV6_FEATURE, \
    KILLSWITCH_FEATURE, \
    NETSHIELD_FEATURE, \
    PORT_FORWARDING_FEATURE, \
    PROTOCOL_FEATURE
from proton.vpn.cli.commands.server import DISCONNECT_COMMAND


CONFIG_COMMAND = "config"
SET_COMMAND = "set"
SETTINGS_LIST_COMMAND = "list"


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
    feature: ClickFeature,
    value: str,
    is_connection_active: bool = False
):
    msg = f"{feature.human_friendly_name} has been set to {value}"

    if feature.requires_restart and is_connection_active:
        msg += ", please establish a new VPN connection for " \
            "changes to take effect."

    msg += _feature_specific_success_postfix(feature, value)

    click.echo(msg)


def _feature_specific_success_postfix(
    feature: ClickFeature,
    value: str,
):
    if feature.command == PORT_FORWARDING_FEATURE.command and \
       value == ToggleType.get_human_friendly_state_string(True):
        return \
            "\nWhen connected to a P2P server, the VPN will request a forwarded port.\n" \
            "To receive and maintain your port, follow the setup guide:\n" \
            "https://protonvpn.com/support/port-forwarding-manual-setup#linux"

    return ""


def _build_config_epilog() -> str:
    lines = [f"""\b
Examples:
  {PROGRAM_NAME} {CONFIG_COMMAND} {SETTINGS_LIST_COMMAND}
  {PROGRAM_NAME} {CONFIG_COMMAND} {SET_COMMAND} {NETSHIELD_FEATURE.command} malware-ads-trackers
  {PROGRAM_NAME} {CONFIG_COMMAND} {SET_COMMAND} {KILLSWITCH_FEATURE.command} standard
  {PROGRAM_NAME} {CONFIG_COMMAND} {SET_COMMAND} {IPV6_FEATURE.command} on
\b
Available Settings:"""]

    for feature in ALL_FEATURES:
        lines.append(f"  {feature.command:<22} {feature.available_setting_description}")

    lines.extend([f"""\b
For setting-specific help:
  {PROGRAM_NAME} {CONFIG_COMMAND} {SET_COMMAND} <setting> --help"""])

    return "\n".join(lines)


@click.group(
    name=CONFIG_COMMAND,
    no_args_is_help=False,
    epilog=_build_config_epilog()
)
def config():
    """Configure Proton VPN settings."""


@config.group(
    name=SET_COMMAND,
    no_args_is_help=False
)
def set_group():
    """Change a specific setting."""


def _format_setting_epilog(feature: ClickFeature) -> str:
    values_with_help = []
    for value_str in feature.click_type.to_list_of_str():
        values_with_help.append(f"  {value_str}   {feature.value_to_help[value_str]}")

    return feature.help_epilog.format(
        feature_values="\n".join(values_with_help),
        program_name=PROGRAM_NAME,
        config_command=CONFIG_COMMAND,
        set_command=SET_COMMAND,
        settings_list_command=SETTINGS_LIST_COMMAND,
        feature_command=feature.command,
    )


def _register_bool_feature_command(group: click.Group, feature: ClickFeature):
    @group.command(
        name=feature.command,
        help=feature.help_description,
        epilog=_format_setting_epilog(feature)
    )
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


@set_group.command(
    name=KILLSWITCH_FEATURE.command,
    help=KILLSWITCH_FEATURE.help_description,
    epilog=_format_setting_epilog(KILLSWITCH_FEATURE)
)
@click.argument("mode", type=click.Choice(KillSwitchType.to_list_of_str(), case_sensitive=False))
@click.pass_context
@run_async
async def killswitch_command(ctx: click.Context, mode: str) -> None:
    """Configure Kill Switch to block internet if VPN connection drops."""
    controller = await Controller.create(params=ctx.obj, click_ctx=ctx)
    if await controller.is_connection_active():
        raise click.UsageError(
            "Disconnect before changing Kill Switch. "
            f"Run '{controller.program_name} {DISCONNECT_COMMAND}' first."
        )

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


@set_group.command(
    name=PROTOCOL_FEATURE.command,
    help=PROTOCOL_FEATURE.help_description,
    epilog=_format_setting_epilog(PROTOCOL_FEATURE)
)
@click.argument(
    "protocol",
    type=click.Choice(ProtocolType.to_list_of_str(), case_sensitive=False),
)
@click.pass_context
@run_async
async def protocol_command(ctx: click.Context, protocol: str) -> None:
    """Select the protocol used to establish the VPN tunnel."""
    controller = await Controller.create(params=ctx.obj, click_ctx=ctx)
    if await controller.is_connection_active():
        raise click.UsageError(
            "Disconnect before changing the protocol. "
            f"Run '{controller.program_name} {DISCONNECT_COMMAND}' first."
        )

    protocol_value = ProtocolType.from_str(protocol)

    try:
        await controller.save_feature_setting(PROTOCOL_FEATURE, protocol_value)
    except AuthenticationRequiredError:
        _raise_error_auth_required(controller, action="set")
    else:
        _print_success_message(
            PROTOCOL_FEATURE,
            ProtocolType.get_human_friendly_state_string(protocol_value)
        )


@set_group.command(
    name=NETSHIELD_FEATURE.command,
    help=NETSHIELD_FEATURE.help_description,
    epilog=_format_setting_epilog(NETSHIELD_FEATURE)
)
@click.argument(
    "mode",
    type=click.Choice(NetshieldType.to_list_of_str(), case_sensitive=False),
)
@click.pass_context
@run_async
async def netshield_command(ctx: click.Context, mode: str) -> None:
    """Configure NetShield ad-blocking and malware protection."""
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


@set_group.command(
    name=CUSTOM_DNS_FEATURE.command,
    help=CUSTOM_DNS_FEATURE.help_description,
    epilog=_format_setting_epilog(CUSTOM_DNS_FEATURE)
)
@click.argument("state", type=click.Choice(ToggleType.to_list_of_str(), case_sensitive=False))
@click.option("--dns", "dns_csv", help="Comma-separated DNS server IPs (IPv4 or IPv6)")
@click.pass_context
@run_async
async def custom_dns_command(ctx: click.Context, state: str, dns_csv: str | None) -> None:
    """Configure custom DNS servers."""
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


@config.command(name=SETTINGS_LIST_COMMAND)
@click.pass_context
@run_async
async def list_features(ctx: click.Context):
    """Show current configuration for all settings."""
    controller = await Controller.create(params=ctx.obj, click_ctx=ctx)

    settings_table = []
    for feature in ALL_FEATURES:
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
        full_set_command_str = f"{controller.program_name} {CONFIG_COMMAND} {SET_COMMAND}"
        help_option_str = ctx.help_option_names[0]
        click.echo(
            f"Use '{full_set_command_str} <setting> <value>' to change settings.\n"
            f"Use '{full_set_command_str} <setting> {help_option_str}' for available values."
        )
