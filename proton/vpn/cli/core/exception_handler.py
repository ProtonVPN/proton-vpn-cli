"""
Exception handling module.

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
from types import TracebackType
from typing import List, Optional, Protocol, Type, Union


class ExceptionReporter(Protocol):  # pylint: disable=too-few-public-methods
    """
    Protocol defining interface for reporting unhandled exceptions
    """
    def report_error(
        self,
        error: Union[
            BaseException,
            tuple[
                Optional[Type[BaseException]],
                Optional[BaseException],
                Optional[TracebackType]
            ]
        ]
    ):
        """
        Reports the provided error
        """
        raise NotImplementedError


class ExceptionHandler:
    """
    Helper class used to silently absorb and/or report specified types of unhandled exceptions
    """

    __absorbed_exceptions: List[BaseException]
    __exception_reporter: Optional[ExceptionReporter] = None

    @staticmethod
    def custom_exception_hook(exc_type, exc_value, exc_traceback):
        """
        When the exception handler is enabled, this method overrides default
        exception handling, dealing with errors that were not explicitly handled.
        :param exc_type: Type of the exception.
        :param exc_value: Instance of the exception. It might be None if the
        exception was triggered using an Exception class, rather than an object
        (e.g. raise Exception, instead of raise Exception()).
        :param exc_traceback: The exception traceback.
        """
        absorb = False
        for absorb_exc in ExceptionHandler.__absorbed_exceptions:
            if issubclass(exc_type, absorb_exc):
                absorb = True
                break

        if not absorb:
            if ExceptionHandler.__exception_reporter and \
               ExceptionHandler.__is_reportable_exception(exc_type):
                ExceptionHandler.__exception_reporter.report_error(
                    (exc_type, exc_value, exc_traceback)
                )

            sys.exit(1)

    @staticmethod
    def __is_reportable_exception(exc_type) -> bool:
        if issubclass(exc_type, AssertionError):
            # We shouldn't catch assertion errors raised by tests.
            return False

        if not issubclass(exc_type, Exception):
            return False

        return True

    @staticmethod
    def asyncio_exception_handler(_, context):
        """
        When the exception handler is enabled, this method overrides default
        asyncio current event loop exception handling,
        dealing with errors that were not explicitly handled.
        """
        exception = context.get('exception', None)
        if exception:
            exc_info = (type(exception), exception, exception.__traceback__)
            ExceptionHandler.custom_exception_hook(*exc_info)

    @staticmethod
    def set_uncaught_exceptions_to_absorb(exceptions: List[BaseException]):
        """
        Silences list of provided exceptions if raised and uncaught
        """
        ExceptionHandler.__absorbed_exceptions = exceptions

    @staticmethod
    def enable(exception_reporter: Optional[ExceptionReporter] = None):
        """
        Enable global handling/absorption/reporting of uncaught exceptions
        """
        ExceptionHandler.__exception_reporter = exception_reporter
        ExceptionHandler.__absorbed_exceptions = []

        sys.excepthook = ExceptionHandler.custom_exception_hook
        asyncio.get_event_loop().set_exception_handler(
            ExceptionHandler.asyncio_exception_handler
        )

    @staticmethod
    def disable():
        """
        Disable global handling/absorption/reporting of uncaught exceptions
        """
        sys.excepthook = sys.__excepthook__
        asyncio.get_event_loop().set_exception_handler(None)  # resets to the default handler
