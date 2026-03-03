"""
Copyright (c) 2026 Proton AG

Provides common CLI command testing fixtures.

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
from proton.vpn.cli.core.controller import Controller, Params


@pytest.fixture
def test_params() -> Params:
    return Params(
        allow_gui_concurrency=True
    )


@pytest.fixture
def test_context(test_params: Params) -> click.Context:
    return click.Context(
        app_cmd,
        obj=test_params,
        info_name="protonvpn"
    )


@pytest.fixture
def controller_mock(test_context: click.Context) -> AsyncMock:
    controller_mock = AsyncMock(spec=Controller)
    type(controller_mock).program_name = \
        PropertyMock(return_value=test_context.info_name)
    test_context.obj.overriding_controller = controller_mock
    return controller_mock


@pytest.fixture
def runner(test_context: click.Context) -> CliRunner:
    with test_context:
        yield CliRunner()


@pytest.fixture
def cli_invoke(runner: CliRunner, test_context: click.Context):
    def _invoke(args: list):
        return runner.invoke(
            app_cmd,
            args,
            parent=test_context,
            standalone_mode=False
        )
    return _invoke
