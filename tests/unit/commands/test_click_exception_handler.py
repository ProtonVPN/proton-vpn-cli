"""
Copyright (c) 2026 Proton AG

Tests for ClickExceptionHandler output formatting.

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
import pytest
import click
from click.exceptions import BadParameter, MissingParameter, UsageError

from proton.vpn.cli import HELP_OPTION
from proton.vpn.cli.commands.feature_setting_definitions import ALL_FEATURES, ClickFeature
from proton.vpn.cli.commands.location_discovery import CITIES_COMMAND, CITIES_LIST_COMMAND
from proton.vpn.cli.commands.settings import CONFIG_COMMAND, SET_COMMAND, config
from proton.vpn.cli.core.click_exception_handler import ClickExceptionHandler


# --- UsageError — missing subcommand ---

def test_group_with_no_subcommand_shows_missing_action_message(
    cli_invoke,
    capsys
):
    result = cli_invoke([CONFIG_COMMAND])

    ClickExceptionHandler.handle_error(result.exception)
    _, err = capsys.readouterr()

    assert f"Error: Missing action for '{CONFIG_COMMAND}' command." in err


def test_group_with_no_subcommand_shows_available_subcommands(
    cli_invoke,
    capsys
):
    result = cli_invoke([CONFIG_COMMAND])

    ClickExceptionHandler.handle_error(result.exception)
    _, err = capsys.readouterr()

    assert "Available actions:" in err
    for subcommand in config.commands:
        assert subcommand in err


def test_group_with_no_subcommand_shows_help_hint(
    cli_invoke,
    capsys
):
    result = cli_invoke([CONFIG_COMMAND])
    command_path = result.exception.ctx.command_path

    ClickExceptionHandler.handle_error(result.exception)
    _, err = capsys.readouterr()

    assert f"Try '{command_path} {HELP_OPTION}' for more information." in err


def test_set_group_with_no_subcommand_lists_all_feature_commands(
    cli_invoke,
    capsys
):
    result = cli_invoke([CONFIG_COMMAND, SET_COMMAND])

    ClickExceptionHandler.handle_error(result.exception)
    _, err = capsys.readouterr()

    assert "Available actions:" in err
    for feature in ALL_FEATURES:
        assert feature.command in err


# --- UsageError — no such command ---

def test_unknown_subcommand_shows_unknown_action_message(
    cli_invoke,
    capsys
):
    bad_cmd = "show"

    result = cli_invoke([CONFIG_COMMAND, bad_cmd])
    assert isinstance(result.exception, UsageError)

    ClickExceptionHandler.handle_error(result.exception)
    _, err = capsys.readouterr()

    assert f"Error: Unknown action '{bad_cmd}' for '{CONFIG_COMMAND}' command." in err


def test_unknown_subcommand_shows_available_actions(
    cli_invoke,
    capsys
):
    bad_cmd = "show"

    result = cli_invoke([CONFIG_COMMAND, bad_cmd])

    ClickExceptionHandler.handle_error(result.exception)
    _, err = capsys.readouterr()

    assert "Available actions:" in err
    for subcommand in config.commands:
        assert subcommand in err


def test_unknown_subcommand_shows_help_hint(
    cli_invoke,
    capsys
):
    bad_cmd = "show"

    result = cli_invoke([CONFIG_COMMAND, bad_cmd])
    command_path = result.exception.ctx.command_path

    ClickExceptionHandler.handle_error(result.exception)
    _, err = capsys.readouterr()

    assert f"Try '{command_path} {HELP_OPTION}' for more information." in err


def test_root_command_with_unknown_subcommand_shows_unknown_action_message(
    cli_invoke,
    capsys
):
    bad_cmd = "badcmd"

    result = cli_invoke([bad_cmd])

    ClickExceptionHandler.handle_error(result.exception)
    _, err = capsys.readouterr()
    context = result.exception.ctx

    assert f"Error: Unknown action '{bad_cmd}' for '{context.info_name}' command." in err


# --- MissingParameter ---

@pytest.mark.parametrize("feature", ALL_FEATURES, ids=[f.command for f in ALL_FEATURES])
def test_missing_value_for_feature_setting_shows_setting_error(
    cli_invoke,
    capsys,
    feature: ClickFeature
):
    result = cli_invoke([CONFIG_COMMAND, SET_COMMAND, feature.command])
    assert isinstance(result.exception, MissingParameter)

    ClickExceptionHandler.handle_error(result.exception)
    _, err = capsys.readouterr()

    assert f"Error: Missing value for '{feature.command}' setting." in err


@pytest.mark.parametrize("feature", ALL_FEATURES, ids=[f.command for f in ALL_FEATURES])
def test_missing_value_for_feature_setting_shows_value_help_pairs(
    cli_invoke,
    capsys,
    feature: ClickFeature
):
    result = cli_invoke([CONFIG_COMMAND, SET_COMMAND, feature.command])

    ClickExceptionHandler.handle_error(result.exception)
    _, err = capsys.readouterr()

    assert "Valid values:" in err
    for value, description in feature.value_to_help.items():
        assert value in err
        assert description in err


@pytest.mark.parametrize("feature", ALL_FEATURES, ids=[f.command for f in ALL_FEATURES])
def test_missing_value_for_feature_setting_shows_help_hint(
    cli_invoke,
    capsys,
    feature: ClickFeature
):
    result = cli_invoke([CONFIG_COMMAND, SET_COMMAND, feature.command])
    command_path = result.exception.ctx.command_path

    ClickExceptionHandler.handle_error(result.exception)
    _, err = capsys.readouterr()

    assert f"Try '{command_path} {HELP_OPTION}' for examples." in err


def test_missing_positional_argument_shows_argument_error(
    cli_invoke,
    capsys
):
    result = cli_invoke([CITIES_COMMAND, CITIES_LIST_COMMAND])
    assert isinstance(result.exception, MissingParameter)

    ClickExceptionHandler.handle_error(result.exception)
    _, err = capsys.readouterr()

    assert "Error: Missing country argument." in err


def test_missing_positional_argument_shows_usage(
    cli_invoke,
    capsys
):
    result = cli_invoke([CITIES_COMMAND, CITIES_LIST_COMMAND])
    command_path = result.exception.ctx.command_path

    ClickExceptionHandler.handle_error(result.exception)
    _, err = capsys.readouterr()

    assert f"Usage: {command_path} <COUNTRY>" in err


def test_missing_positional_argument_shows_help_hint(
    cli_invoke,
    capsys
):
    result = cli_invoke([CITIES_COMMAND, CITIES_LIST_COMMAND])
    command_path = result.exception.ctx.command_path

    ClickExceptionHandler.handle_error(result.exception)
    _, err = capsys.readouterr()

    assert f"Try '{command_path} {HELP_OPTION}' for examples." in err


# --- BadParameter ---

@pytest.mark.parametrize("feature", ALL_FEATURES, ids=[f.command for f in ALL_FEATURES])
def test_invalid_value_for_feature_setting_shows_invalid_value_error(
    cli_invoke,
    capsys,
    feature: ClickFeature
):
    bad_value = "invalid_value"

    result = cli_invoke([CONFIG_COMMAND, SET_COMMAND, feature.command, bad_value])
    assert isinstance(result.exception, BadParameter)

    ClickExceptionHandler.handle_error(result.exception)
    _, err = capsys.readouterr()

    assert f"Error: Invalid value '{bad_value}' for '{feature.command}'." in err


@pytest.mark.parametrize("feature", ALL_FEATURES, ids=[f.command for f in ALL_FEATURES])
def test_invalid_value_for_feature_setting_shows_value_help_pairs(
    cli_invoke,
    capsys,
    feature: ClickFeature
):
    bad_value = "invalid_value"

    result = cli_invoke([CONFIG_COMMAND, SET_COMMAND, feature.command, bad_value])

    ClickExceptionHandler.handle_error(result.exception)
    _, err = capsys.readouterr()

    assert "Valid values:" in err
    for value, description in feature.value_to_help.items():
        assert value in err
        assert description in err


@pytest.mark.parametrize("feature", ALL_FEATURES, ids=[f.command for f in ALL_FEATURES])
def test_invalid_value_for_feature_setting_shows_help_hint(
    cli_invoke,
    capsys,
    feature: ClickFeature
):
    bad_value = "invalid_value"

    result = cli_invoke([CONFIG_COMMAND, SET_COMMAND, feature.command, bad_value])
    command_path = result.exception.ctx.command_path

    ClickExceptionHandler.handle_error(result.exception)
    _, err = capsys.readouterr()

    assert f"Try '{command_path} {HELP_OPTION}' for examples." in err


# --- ClickException ---

def test_click_exception_shows_error_message(capsys):
    msg = "something went wrong"

    assert ClickExceptionHandler.handle_error(click.ClickException(msg)) is True

    _, err = capsys.readouterr()
    assert f"Error: {msg}" in err


# --- Unrecognised exceptions ---

def test_unrecognised_exception_returns_false():
    assert ClickExceptionHandler.handle_error(Exception("unexpected")) is False


def test_usage_error_without_context_shows_error_message(capsys):
    msg = "some usage error"
    assert ClickExceptionHandler.handle_error(UsageError(msg)) is True
    _, err = capsys.readouterr()
    assert f"Error: {msg}" in err
