"""
Copyright (c) 2026 Proton AG

Provides CLI command testing for settings command help content.

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

from proton.vpn.cli import app as app_cmd, HELP_OPTION
from proton.vpn.cli.commands.feature_setting_definitions import \
    ALL_FEATURES, \
    NETSHIELD_FEATURE, \
    KILLSWITCH_FEATURE, \
    IPV6_FEATURE, \
    VPN_ACCELERATOR_FEATURE, \
    ANON_CRASH_REPORTS_FEATURE, \
    PORT_FORWARDING_FEATURE, \
    CUSTOM_DNS_FEATURE, \
    MODERATE_NAT_FEATURE, \
    ClickFeature
from proton.vpn.cli.commands.settings import \
    CONFIG_COMMAND, \
    SET_COMMAND, \
    SETTINGS_LIST_COMMAND


_FEATURES_WITH_CURRENT_SETTING_GUIDANCE = [
    NETSHIELD_FEATURE,
    KILLSWITCH_FEATURE,
    CUSTOM_DNS_FEATURE,
    VPN_ACCELERATOR_FEATURE,
    MODERATE_NAT_FEATURE,
    IPV6_FEATURE,
    ANON_CRASH_REPORTS_FEATURE
]

_FEATURES_WITH_HOW_IT_WORKS = [
    NETSHIELD_FEATURE,
    PORT_FORWARDING_FEATURE,
    VPN_ACCELERATOR_FEATURE,
    MODERATE_NAT_FEATURE,
    IPV6_FEATURE,
    ANON_CRASH_REPORTS_FEATURE
]


def _content_lines_under(epilog: str, heading: str) -> list[str]:
    """Extract all non-empty content lines under the given section heading.

    Sections are delimited by \\b (chr(8)), which click uses as a paragraph
    separator in epilog strings.
    """
    idx = epilog.find(heading)
    if idx == -1:
        return []
    rest = epilog[idx + len(heading):]
    # Section ends at the next \b (section separator) or end of string
    section_content = rest.split("\b")[0]
    return [
        line.strip()
        for line in section_content.splitlines()
        if line.strip() and line.strip() != "\b"
    ]


# --- config group help ---

def test_config_help_shows_available_settings_section(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CONFIG_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Available Settings:" in result.output


def test_config_help_lists_all_feature_commands(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CONFIG_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    for feature in ALL_FEATURES:
        assert feature.command in result.output


def test_config_help_lists_all_feature_descriptions(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CONFIG_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    for feature in ALL_FEATURES:
        assert feature.available_setting_description in result.output


def test_config_help_shows_examples_section(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CONFIG_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Examples:" in result.output
    assert SETTINGS_LIST_COMMAND in result.output
    assert f"{NETSHIELD_FEATURE.command} malware-ads-trackers" in result.output
    assert f"{KILLSWITCH_FEATURE.command} standard" in result.output
    assert f"{IPV6_FEATURE.command} on" in result.output


def test_config_help_shows_setting_specific_help_guidance(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CONFIG_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "For setting-specific help:" in result.output
    assert SET_COMMAND in result.output
    assert HELP_OPTION in result.output


# --- config list help ---

def test_config_list_help_shows_description(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CONFIG_COMMAND, SETTINGS_LIST_COMMAND, HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Show current configuration for all settings." in result.output


# --- config set <feature> help ---

@pytest.mark.parametrize("feature", ALL_FEATURES)
def test_config_set_feature_help_shows_help_description(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock,
    feature: ClickFeature
):
    result = runner.invoke(
        app_cmd,
        [CONFIG_COMMAND,
         SET_COMMAND,
         feature.command,
         HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert feature.help_description in result.output


@pytest.mark.parametrize("feature", ALL_FEATURES)
def test_config_set_feature_help_shows_all_valid_values(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock,
    feature: ClickFeature
):
    result = runner.invoke(
        app_cmd,
        [CONFIG_COMMAND,
         SET_COMMAND,
         feature.command,
         HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    for value in feature.click_type.to_list_of_str():
        assert value in result.output


@pytest.mark.parametrize("feature", ALL_FEATURES)
def test_config_set_feature_help_shows_value_descriptions(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock,
    feature: ClickFeature
):
    result = runner.invoke(
        app_cmd,
        [CONFIG_COMMAND,
         SET_COMMAND,
         feature.command,
         HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    for value_description in feature.value_to_help.values():
        assert value_description.strip() in result.output


@pytest.mark.parametrize("feature", ALL_FEATURES)
def test_config_set_feature_help_shows_examples_section(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock,
    feature: ClickFeature
):
    result = runner.invoke(
        app_cmd,
        [CONFIG_COMMAND,
         SET_COMMAND,
         feature.command,
         HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Examples:" in result.output
    assert feature.command in result.output


@pytest.mark.parametrize(
    "feature",
    _FEATURES_WITH_CURRENT_SETTING_GUIDANCE
)
def test_config_set_feature_help_shows_current_setting_guidance(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock,
    feature: ClickFeature
):
    result = runner.invoke(
        app_cmd,
        [CONFIG_COMMAND,
         SET_COMMAND,
         feature.command,
         HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Current Setting:" in result.output
    assert SETTINGS_LIST_COMMAND in result.output


@pytest.mark.parametrize(
    "feature",
    _FEATURES_WITH_HOW_IT_WORKS
)
def test_config_set_feature_help_shows_how_it_works_section(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock,
    feature: ClickFeature
):
    result = runner.invoke(
        app_cmd,
        [CONFIG_COMMAND,
         SET_COMMAND,
         feature.command,
         HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "How It Works:" in result.output
    for line in _content_lines_under(feature.help_epilog, "How It Works:"):
        assert line in result.output


def test_config_set_vpn_accelerator_help_shows_recommendation(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CONFIG_COMMAND,
         SET_COMMAND,
         VPN_ACCELERATOR_FEATURE.command,
         HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Recommendation:" in result.output
    for line in _content_lines_under(VPN_ACCELERATOR_FEATURE.help_epilog, "Recommendation:"):
        assert line in result.output


def test_config_set_anon_crash_reports_help_shows_privacy_section(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CONFIG_COMMAND,
         SET_COMMAND,
         ANON_CRASH_REPORTS_FEATURE.command,
         HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Privacy:" in result.output
    for line in _content_lines_under(ANON_CRASH_REPORTS_FEATURE.help_epilog, "Privacy:"):
        assert line in result.output


def test_config_set_port_forwarding_help_shows_setup_guide(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CONFIG_COMMAND,
         SET_COMMAND,
         PORT_FORWARDING_FEATURE.command,
         HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Setup Guide:" in result.output
    for line in _content_lines_under(PORT_FORWARDING_FEATURE.help_epilog, "Setup Guide:"):
        assert line in result.output


def test_config_set_kill_switch_help_shows_behavior_section(
    runner: CliRunner,
    test_context: click.Context,
    controller_mock: AsyncMock
):
    result = runner.invoke(
        app_cmd,
        [CONFIG_COMMAND,
         SET_COMMAND,
         KILLSWITCH_FEATURE.command,
         HELP_OPTION],
        parent=test_context
    )

    assert result.exit_code == 0
    assert "Behavior:" in result.output
    for line in _content_lines_under(KILLSWITCH_FEATURE.help_epilog, "Behavior:"):
        assert line in result.output
