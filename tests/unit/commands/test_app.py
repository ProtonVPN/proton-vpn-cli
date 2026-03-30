"""
Copyright (c) 2026 Proton AG

Tests for main() exit code behaviour.

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
from typing import Optional
from unittest.mock import AsyncMock
import pytest

from proton.session.exceptions import ProtonAPIError, ProtonAPINotReachable
from proton.vpn.cli import main
from proton.vpn.cli.commands.account import SIGNIN_COMMAND
from proton.vpn.cli.commands.settings import CONFIG_COMMAND
from proton.vpn.cli.core.exceptions import SignoutRequiredError


def _run_main(
    args: list[str],
    controller_mock: Optional[AsyncMock] = None,
    capsys=None
) -> tuple[int, str]:
    """Invoke main() with the given CLI args and return (exit_code, stderr)."""
    with pytest.raises(SystemExit) as exc_info:
        main(cli_args=args, allow_concurrency=True, controller=controller_mock)
    stderr = capsys.readouterr().err if capsys is not None else ""
    return exc_info.value.code, stderr


# --- UsageError ---


def test_missing_subcommand_exits_with_code_2():
    exit_code, _ = _run_main([CONFIG_COMMAND])
    assert exit_code == 2


def test_unknown_subcommand_exits_with_code_2():
    exit_code, _ = _run_main([CONFIG_COMMAND, "badcmd"])
    assert exit_code == 2


# --- ProtonAPIError ---


def test_proton_api_error_is_displayed_and_exits_cleanly(
    controller_mock: AsyncMock,
    capsys
):
    error = ProtonAPIError(401, {}, {"Code": 8002, "Error": "Invalid credentials"})

    def login(*_):
        raise error

    controller_mock.login.side_effect = login

    exit_code, stderr = _run_main([SIGNIN_COMMAND, "account_name"], controller_mock, capsys)

    assert exit_code == 1
    assert f"Error: {error.message}" in stderr


# --- ProtonAPINotReachable ---


def test_proton_api_not_reachable_is_displayed_and_exits_cleanly(
    controller_mock: AsyncMock,
    capsys
):
    def login(*_):
        raise ProtonAPINotReachable("Network error")

    controller_mock.login.side_effect = login

    exit_code, _ = _run_main([SIGNIN_COMMAND, "account_name"], controller_mock)

    output = capsys.readouterr()
    assert exit_code == 1
    assert "Error: Network connectivity issues detected. "\
           "Please check your internet connection and try again." in output.out


# --- TimeoutError ---


def test_timeout_error_is_displayed_and_exits_cleanly(
    controller_mock: AsyncMock,
    capsys
):
    def login(*_):
        raise TimeoutError("Connection timed out")

    controller_mock.login.side_effect = login

    exit_code, _ = _run_main([SIGNIN_COMMAND, "account_name"], controller_mock)

    output = capsys.readouterr()
    assert exit_code == 1
    assert "Error: Network connectivity issues detected. "\
           "Please check your internet connection and try again." in output.out


# --- unexpected Exception ---


def test_unexpected_exception_shows_error_message_and_reraises(
    controller_mock: AsyncMock,
    capsys
):
    def login(*_):
        raise RuntimeError("Something went wrong")

    controller_mock.login.side_effect = login

    with pytest.raises(RuntimeError):
        main(cli_args=[SIGNIN_COMMAND, "account_name"], allow_concurrency=True, controller=controller_mock)

    output = capsys.readouterr()
    assert output.out == (
        "An unexpected error occurred. Please try again.\n"
        "If the error persists please contact customer support: "
        "https://protonvpn.com/support/contact?"
        "subject=%5BCLI%5D&os=Linux&platform=VPN%20for%20Linux\n"
    )


# --- click exception ---


def test_signin_when_authenticated_exits_with_code_1(controller_mock: AsyncMock):
    def login(*_):
        raise SignoutRequiredError

    controller_mock.login.side_effect = login

    exit_code, _ = _run_main([SIGNIN_COMMAND, "account_name"], controller_mock)
    assert exit_code == 1
