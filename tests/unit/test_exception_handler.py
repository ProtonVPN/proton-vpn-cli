"""
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
import asyncio
import sys
from unittest.mock import Mock
import pytest

from proton.vpn.cli.core.exception_handler import ExceptionHandler


@pytest.mark.asyncio
async def test_enable_exception_handler_adds_excepthooks():
    ExceptionHandler.enable()

    assert sys.excepthook is ExceptionHandler.custom_exception_hook
    assert asyncio.get_event_loop().get_exception_handler() is \
        ExceptionHandler.asyncio_exception_handler

    ExceptionHandler.disable()


@pytest.mark.asyncio
async def test_disable_exception_handler_removes_excepthooks():
    original_sys_excepthook = sys.excepthook
    orignal_asyncio_exception_handler = asyncio.get_event_loop().get_exception_handler()

    ExceptionHandler.enable()
    ExceptionHandler.disable()

    assert sys.excepthook is original_sys_excepthook
    assert asyncio.get_event_loop().get_exception_handler() is orignal_asyncio_exception_handler


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "exception_type, is_handled", [
        (KeyboardInterrupt, False),  # Exception not inheriting Exception class
        (AssertionError, False),  # AssertionErrors used in tests should be reraised as well
        (Exception, True)
    ]
)
async def test_exception_handling_reports_exceptions_when_relevant(exception_type, is_handled):
    reporter = Mock()
    ExceptionHandler.enable(exception_reporter=reporter)

    with pytest.raises(SystemExit):
        sys.excepthook(
            exception_type,
            exception_type(),
            None
        )

    if is_handled:
        reporter.report_error.assert_called_once()
    else:
        reporter.report_error.assert_not_called()

    ExceptionHandler.disable()


@pytest.mark.asyncio
async def test_exception_handling_absorbs_silenced_exceptions():
    reporter = Mock()
    ExceptionHandler.enable(exception_reporter=reporter)

    ExceptionHandler.set_uncaught_exceptions_to_absorb([Exception])
    sys.excepthook(
        Exception,
        Exception(),
        None
    )
    reporter.report_error.assert_not_called()

    ExceptionHandler.disable()
