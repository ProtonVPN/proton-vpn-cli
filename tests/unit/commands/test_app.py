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

from proton.vpn.cli import main
from proton.vpn.cli.commands.account import SIGNIN_COMMAND
from proton.vpn.cli.commands.settings import CONFIG_COMMAND
from proton.vpn.cli.core.exceptions import SignoutRequiredError


def _run_main(
    args: list[str],
    controller_mock: Optional[AsyncMock] = None
) -> int:
    """Invoke main() with the given CLI args and return the SystemExit code."""
    with pytest.raises(SystemExit) as exc_info:
        main(cli_args=args, allow_concurrency=True, controller=controller_mock)
    return exc_info.value.code


# --- UsageError ---


def test_missing_subcommand_exits_with_code_2():
    assert _run_main([CONFIG_COMMAND]) == 2


def test_unknown_subcommand_exits_with_code_2():
    assert _run_main([CONFIG_COMMAND, "badcmd"]) == 2


# --- click exception ---


def test_signin_when_authenticated_exits_with_code_1(controller_mock: AsyncMock):
    def login(*_):
        raise SignoutRequiredError

    controller_mock.login.side_effect = login

    assert _run_main([SIGNIN_COMMAND, "account_name"], controller_mock) == 1
