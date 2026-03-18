"""
Exceptions raised by the CLI.

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


class VPNConnectionError(Exception):
    """
    Error establishing a VPN server connection
    """


class VPNConnection2FARequiredError(VPNConnectionError):
    """
    Raised when VPN 2FA is required
    """


class CountryCodeError(Exception):
    """
    Error identifying a country by code
    """


class CountryNameError(Exception):
    """
    Error identifying a country by name
    """


class AuthenticationRequiredError(Exception):
    """
    Error performing operation that requires user authentication
    """


class AuthenticationFailedError(Exception):
    """
    Error occured during authentication
    """


class Authentication2FAFailedError(Exception):
    """
    Error occured during 2FA authentication
    """


class SignoutRequiredError(Exception):
    """
    Error performing operation requiring the user to be signed out
    """


class RequiresHigherTierError(Exception):
    """
    Requested feature that requires a higher tier
    """


class InvalidDNS(Exception):
    """Raised when user provides invalid DNS value
    """
    def __init__(self, dns: str, message: str):
        self.dns = dns
        self.message = message
