"""
Copyright (c) 2026 Proton AG

Provides CLI command testing for settings configuration.

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
from unittest.mock import AsyncMock, PropertyMock
import pytest

import click
from click.testing import CliRunner

from proton.vpn.cli import app as app_cmd
from proton.vpn.cli.commands.account import SIGNIN_COMMAND, SIGNOUT_COMMAND
from proton.vpn.cli.commands.feature_setting_definitions import \
    ALL_FEATURES, \
    PORT_FORWARDING_FEATURE, \
    CUSTOM_DNS_FEATURE, \
    KILLSWITCH_FEATURE, \
    NetshieldType, \
    CustomDNSType, \
    ClickFeature
from proton.vpn.cli.commands.server import DISCONNECT_COMMAND
from proton.vpn.cli.commands.settings import \
    CONFIG_COMMAND, \
    SET_COMMAND, \
    SETTINGS_LIST_COMMAND
from proton.vpn.cli.core.exceptions import \
    AuthenticationRequiredError, \
    RequiresHigherTierError, \
    InvalidDNS
from proton.vpn.core.settings.custom_dns import CustomDNS
from proton.vpn.killswitch.interface import KillSwitchState


def test_setting_all_features_fails_when_not_signed_in(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    def save_feature_setting(*_):
        raise AuthenticationRequiredError

    controller_mock.save_feature_setting.side_effect = save_feature_setting
    controller_mock.is_connection_active.return_value = False

    for feature in ALL_FEATURES:
        value = feature.click_type.to_list_of_str()[0]
        result = runner.invoke(
            app_cmd,
            [CONFIG_COMMAND,
             SET_COMMAND,
             feature.command,
             value],
            parent=test_context
        )

        assert result.exit_code == 2
        assert f"Authentication required to set feature status. " \
               f"Please sign in with '{test_context.info_name} {SIGNIN_COMMAND}'" \
               in result.output


def test_setting_all_paying_features_fails_when_requiring_higher_tier(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    def save_feature_setting(*_):
        raise RequiresHigherTierError

    controller_mock.save_feature_setting.side_effect = save_feature_setting

    for feature in ALL_FEATURES:
        if feature.available_on_free_tier:
            continue

        first_value = feature.click_type.to_list_of_str()[0]
        result = runner.invoke(
            app_cmd,
            [CONFIG_COMMAND,
             SET_COMMAND,
             feature.command,
             first_value],
            parent=test_context
        )

        assert result.exit_code == 2
        assert f"{feature.human_friendly_name} feature is not available " \
               "on your current subscription plan. " \
               "Please upgrade to access this feature." \
               in result.output


def test_setting_all_features_shows_message_confirming_success(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    controller_mock.is_connection_active.return_value = False

    for feature in ALL_FEATURES:
        first_value_str = feature.click_type.to_list_of_str()[0]
        first_value_setting = feature.click_type.from_str(first_value_str)
        result = runner.invoke(
            app_cmd,
            [CONFIG_COMMAND,
             SET_COMMAND,
             feature.command,
             first_value_str],
            parent=test_context
        )

        human_friendly_value_str = \
            feature.click_type.get_human_friendly_state_string(first_value_setting)

        if isinstance(feature.click_type, NetshieldType):
            human_friendly_value_str = f"'{human_friendly_value_str}'"

        assert result.exit_code == 0
        assert f"{feature.human_friendly_name} has been set to {human_friendly_value_str}" \
               in result.output


def test_setting_all_features_explains_reconnection_required_for_relevant_features_when_connected(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    controller_mock.is_connection_active.return_value = True

    for feature in ALL_FEATURES:
        if feature.requires_restart:
            first_value_str = feature.click_type.to_list_of_str()[0]
            result = runner.invoke(
                app_cmd,
                [CONFIG_COMMAND,
                 SET_COMMAND,
                 feature.command,
                 first_value_str],
                parent=test_context
            )

            assert result.exit_code == 0

            assert ", please establish a new VPN connection for changes to take effect." \
                   in result.output


def test_setting_custom_dns_fails_when_not_provided_with_dns_option(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CONFIG_COMMAND,
         SET_COMMAND,
         CUSTOM_DNS_FEATURE.command,
         CUSTOM_DNS_FEATURE.click_type.to_str(CustomDNS(enabled=True))],
        parent=test_context
    )

    assert result.exit_code == 2
    assert f"When enabling {CUSTOM_DNS_FEATURE.human_friendly_name} feature " \
           "you must provide a list of comma separated DNS's." \
           in result.output


def test_setting_custom_dns_fails_when_not_provided_with_valid_ips(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    def parse_dns_ips(*_):
        raise InvalidDNS("invalid_ip", "")

    controller_mock.parse_dns_ips.side_effect = parse_dns_ips

    result = runner.invoke(
        app_cmd,
        [CONFIG_COMMAND,
         SET_COMMAND,
         CUSTOM_DNS_FEATURE.command,
         CUSTOM_DNS_FEATURE.click_type.to_str(CustomDNS(enabled=True)),
         "--dns",
         "invalid_ip"],
        parent=test_context
    )

    assert result.exit_code == 2
    assert "Invalid DNS address 'invalid_ip'. Please provide a valid IPv4 address." \
           in result.output


def test_enabling_port_forwarding_informs_of_required_manual_setup(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CONFIG_COMMAND,
         SET_COMMAND,
         PORT_FORWARDING_FEATURE.command,
         PORT_FORWARDING_FEATURE.click_type.to_str(True)],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "\nWhen connected to a P2P server, the VPN will request a forwarded port.\n" \
           "To receive and maintain your port, follow the setup guide:\n" \
           "https://protonvpn.com/support/port-forwarding-manual-setup#linux" \
           in result.output


@pytest.mark.parametrize(
    "is_connected, killswitch_state",
    [
        (True, KillSwitchState.OFF),
        (True, KillSwitchState.ON),
        (False, KillSwitchState.OFF),
        (False, KillSwitchState.ON),
    ]
)
def test_modifying_killswitch_only_succeeds_when_disconnected(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock,
    is_connected: bool,
    killswitch_state: KillSwitchState
):
    controller_mock.is_connection_active.return_value = is_connected

    result = runner.invoke(
        app_cmd,
        [CONFIG_COMMAND,
         SET_COMMAND,
         KILLSWITCH_FEATURE.command,
         KILLSWITCH_FEATURE.click_type.to_str(killswitch_state)],
        parent=test_context
    )

    assert result.exit_code == (2 if is_connected else 0)
    assert ("Disconnect before changing Kill Switch. "
            f"Run '{test_context.info_name} {DISCONNECT_COMMAND}' first."
            in result.output) == is_connected


def test_listing_all_settings_fails_when_not_signed_in(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    def get_feature_setting(*_):
        raise AuthenticationRequiredError

    controller_mock.get_feature_setting.side_effect = get_feature_setting

    result = runner.invoke(
        app_cmd,
        [CONFIG_COMMAND, SETTINGS_LIST_COMMAND],
        parent=test_context
    )

    assert result.exit_code == 2
    assert f"Authentication required to view feature status. " \
           f"Please sign in with '{test_context.info_name} {SIGNIN_COMMAND}'" \
           in result.output


def test_listing_all_settings_shows_free_user_which_settings_require_higher_tier(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    def get_feature_setting(feature: ClickFeature):
        if isinstance(feature.click_type, CustomDNSType):
            return CustomDNS(enabled=True)

        first_value_str = feature.click_type.to_list_of_str()[0]
        first_value_setting = feature.click_type.from_str(first_value_str)
        return first_value_setting

    controller_mock.get_feature_setting.side_effect = get_feature_setting
    type(controller_mock).user_on_free_tier = PropertyMock(return_value=True)

    result = runner.invoke(
        app_cmd,
        [CONFIG_COMMAND, SETTINGS_LIST_COMMAND],
        parent=test_context
    )

    for feature in ALL_FEATURES:
        matched_feature_line = \
            [line for line in result.output.split('\n') if feature.command in line][0]

        if feature.available_on_free_tier:
            assert "Upgrade to enable" not in matched_feature_line
        else:
            assert "Upgrade to enable" in matched_feature_line

    assert result.exit_code == 0


def test_listing_all_settings_shows_correct_setting_per_feature(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    def get_feature_setting(feature: ClickFeature):
        if isinstance(feature.click_type, CustomDNSType):
            return CustomDNS(enabled=True)

        first_value_str = feature.click_type.to_list_of_str()[0]
        first_value_setting = feature.click_type.from_str(first_value_str)
        return first_value_setting

    controller_mock.get_feature_setting.side_effect = get_feature_setting
    type(controller_mock).user_on_free_tier = PropertyMock(return_value=False)

    result = runner.invoke(
        app_cmd,
        [CONFIG_COMMAND, SETTINGS_LIST_COMMAND],
        parent=test_context
    )

    for feature in ALL_FEATURES:
        matched_feature_line = \
            [line for line in result.output.split('\n') if feature.command in line][0]

        assert feature.click_type.to_str(get_feature_setting(feature)) in matched_feature_line

    assert result.exit_code == 0


@pytest.mark.parametrize("free_user", [True, False])
def test_listing_all_settings_shows_correct_guidance_for_user_tier(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock,
    free_user: bool
):
    def get_feature_setting(feature: ClickFeature):
        if isinstance(feature.click_type, CustomDNSType):
            return CustomDNS(enabled=True)

        first_value_str = feature.click_type.to_list_of_str()[0]
        first_value_setting = feature.click_type.from_str(first_value_str)
        return first_value_setting

    controller_mock.get_feature_setting.side_effect = get_feature_setting
    type(controller_mock).user_on_free_tier = PropertyMock(return_value=free_user)

    result = runner.invoke(
        app_cmd,
        [CONFIG_COMMAND, SETTINGS_LIST_COMMAND],
        parent=test_context
    )

    program_name = test_context.info_name

    if free_user:
        assert \
            "To upgrade to VPN Plus visit: https://account.protonvpn.com/pricing\n" \
            "After upgrading online:\n" \
            "    Sign out and sign in again to activate your new plan:\n" \
            f"    {program_name} {SIGNOUT_COMMAND} && {program_name} {SIGNIN_COMMAND}" \
            in result.output
    else:
        full_set_command_str = f"{program_name} {CONFIG_COMMAND} {SET_COMMAND}"
        help_option_str = test_context.help_option_names[0]
        assert \
            f"Use '{full_set_command_str} <setting> <value>' to change settings.\n" \
            f"Use '{full_set_command_str} <setting> {help_option_str}' for available values." \
            in result.output

    assert result.exit_code == 0
