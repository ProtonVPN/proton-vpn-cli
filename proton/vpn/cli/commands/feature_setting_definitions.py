"""
Feature command definitions for config set subcommands.

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
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol

from proton.vpn.killswitch.interface import KillSwitchState
from proton.vpn.core.settings.features import NetShield
from proton.vpn.core.settings.custom_dns import CustomDNS
from proton.vpn.cli.core.controller import Feature


class ClickArgType(Protocol):
    """Maps between VPN state types and click friendly formats"""

    @staticmethod
    @abstractmethod
    def get_human_friendly_state_string(value: Any) -> str:
        """Returns human friendly state string for the specified value."""
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def to_list_of_str() -> list[str]:
        """Converts to a list of all possible click value strings

        This is a necessary change because <8.2.0, `click.Choice`
        can only take a list of strings. With version >=8.2.0 click
        supports non-string choices (you can pass an enum class).
        This change is to make it backwards compatible, as on Fedora 43
        click is v8.1.7 and on Ubuntu 24.04 v8.1.6.
        See more here: https://click.palletsprojects.com/en/stable/api/#click.Choice
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def from_str(value: str) -> Any:
        """Returns value based on provided click string"""
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def to_str(value: Any) -> str:
        """Returns click string based on provided value"""
        raise NotImplementedError


class ToggleType(ClickArgType):
    """Represents simple binary options that a user can select."""

    @staticmethod
    def get_human_friendly_state_string(value: bool) -> str:
        """Returns human friendly state string for the specified value."""
        if value is False:
            return "disabled"

        return "enabled"

    @staticmethod
    def to_list_of_str() -> list[str]:
        """Converts to a list of all possible click value strings"""
        return ["off", "on"]

    @staticmethod
    def from_str(value: str) -> bool:
        """Returns value based on provided click string"""
        if value.lower() == "off":
            return False

        return True

    @staticmethod
    def to_str(value: bool) -> str:
        """Returns click string based on provided value"""
        if value is False:
            return "off"

        return "on"


class CustomDNSType(ToggleType):
    """Toggle extension for CustomDNS"""

    @staticmethod
    def to_str(value: CustomDNS) -> str:
        """Returns click string based on provided value"""
        enabled = ToggleType.to_str(value.enabled)

        max_ip_list_length = 2
        if value.ip_list:
            ips = value.ip_list[:max_ip_list_length]
            ips_to_show = [str(dns.ip) for dns in ips]
            if len(value.ip_list) > max_ip_list_length:
                ips_to_show.append("...")
            return f"{enabled}  [{', '.join(ips_to_show)}]"

        # no DNS IPs to show
        return enabled


class KillSwitchType(ClickArgType):
    """Represents the various kill switch states that a user can select"""
    # Advanced option is temporarily removed as
    # currently it's not possible to establish a connection with it enabled,
    # while being disconnected.

    @staticmethod
    def get_human_friendly_state_string(value: KillSwitchState) -> str:
        """Returns human friendly state string for the specified value."""
        if value == KillSwitchState.OFF:
            return "disabled"

        return "standard"

    @staticmethod
    def to_list_of_str() -> list[str]:
        """Converts to a list of all possible click value strings

        See explanation above.
        """
        return ["off", "standard"]

    @staticmethod
    def from_str(value: str) -> KillSwitchState:
        """Returns value based on provided click string"""
        if value.upper() == KillSwitchState.OFF.name:
            return KillSwitchState.OFF

        return KillSwitchState.ON

    @staticmethod
    def to_str(value: KillSwitchState) -> str:
        """Returns click string based on provided value"""
        if value == KillSwitchState.OFF:
            return "off"

        return "standard"


class NetshieldType(ClickArgType):
    """Represent the various netshield states that a user can select"""
    @staticmethod
    def get_human_friendly_state_string(value: NetShield) -> str:
        """Returns human friendly state string for the specified value."""
        if value == NetShield.NO_BLOCK:
            return "disabled"

        if value == NetShield.BLOCK_MALICIOUS_URL:
            return "malware only"

        return "malware, ads and trackers"

    @staticmethod
    def to_list_of_str() -> list[str]:
        """Converts to a list of all possible click value strings"""
        return ["off", "malware-only", "malware-ads-trackers"]

    @staticmethod
    def from_str(value: str) -> NetShield:
        """Returns value based on provided click string"""
        if value == "off":
            return NetShield.NO_BLOCK

        if value == "malware-only":
            return NetShield.BLOCK_MALICIOUS_URL

        return NetShield.BLOCK_ADS_AND_TRACKING

    @staticmethod
    def to_str(value: NetShield) -> str:
        """Returns click string based on provided value"""
        if value == NetShield.NO_BLOCK:
            return "off"

        if value == NetShield.BLOCK_MALICIOUS_URL:
            return "malware-only"

        return "malware-ads-trackers"


WIREGUARD = "wireguard"
OPENVPN_UDP = "openvpn-udp"
OPENVPN_TCP = "openvpn-tcp"

_PROTOCOL_TO_HUMAN_FRIENDLY_NAME = {
    WIREGUARD: "WireGuard",
    OPENVPN_UDP: "OpenVPN (UDP)",
    OPENVPN_TCP: "OpenVPN (TCP)",
}


class ProtocolType(ClickArgType):
    """Represents the VPN protocols that a user can select."""

    @staticmethod
    def get_human_friendly_state_string(value: str) -> str:
        """Returns human friendly state string for the specified value."""
        return _PROTOCOL_TO_HUMAN_FRIENDLY_NAME[value]

    @staticmethod
    def to_list_of_str() -> list[str]:
        """Converts to a list of all possible click value strings"""
        return list(_PROTOCOL_TO_HUMAN_FRIENDLY_NAME)

    @staticmethod
    def from_str(value: str) -> str:
        """Returns value based on provided click string"""
        return value.lower()

    @staticmethod
    def to_str(value: str) -> str:
        """Returns click string based on provided value"""
        return value


@dataclass
class ClickFeature(Feature):
    """Click specific feature data."""
    command: str = None
    human_friendly_name: str = None
    available_setting_description: str = None
    help_description: str = None
    help_epilog: str = None
    value_to_help: dict[str, str] = None
    click_type: ClickArgType = None


VPN_ACCELERATOR_FEATURE = ClickFeature(
    command="vpn-accelerator",
    human_friendly_name="VPN Accelerator",
    setting_path="features.vpn_accelerator",
    available_setting_description="Performance optimization",
    help_description="Enable or disable VPN Accelerator for improved connection speeds.",
    value_to_help={
        "off": "Disable VPN Accelerator",
        "on": " Enable VPN Accelerator (recommended)"
    },
    help_epilog="""\b
Values:
{feature_values}
\b
Examples:
  {program_name} {config_command} {set_command} {feature_command} on
  {program_name} {config_command} {set_command} {feature_command} off
\b
Current Setting:
  Run '{program_name} {config_command} {settings_list_command}' to see current value.
\b
How It Works:
  VPN Accelerator uses advanced technologies to increase VPN speeds
  by up to 400% without compromising security. It optimizes the
  connection between your device and Proton VPN servers.
\b
Recommendation:
  Keep enabled for best performance. Only disable if experiencing
  connection issues with specific networks.""",
    click_type=ToggleType()
)


MODERATE_NAT_FEATURE = ClickFeature(
    command="moderate-nat",
    human_friendly_name="Moderate NAT",
    setting_path="features.moderate_nat",
    available_setting_description="NAT type for gaming/P2P",
    help_description="Enable or disable Moderate NAT for improved gaming and P2P performance.",
    value_to_help={
        "off": "Disable Moderate NAT (Strict NAT)",
        "on": " Enable Moderate NAT"
    },
    help_epilog="""\b
Values:
{feature_values}
\b
Examples:
  {program_name} {config_command} {set_command} {feature_command} on
  {program_name} {config_command} {set_command} {feature_command} off
\b
Current Setting:
  Run '{program_name} {config_command} {settings_list_command}' to see current value.
\b
How It Works:
  NAT (Network Address Translation) type affects your ability to connect
  to other players in online games and peers in P2P networks.

  Strict NAT (off): Maximum security, may limit connections in games/P2P
  Moderate NAT (on): Better connectivity for gaming and P2P, still secure""",
    click_type=ToggleType()
)


IPV6_FEATURE = ClickFeature(
    command="ipv6",
    human_friendly_name="IPv6",
    setting_path="ipv6",
    available_on_free_tier=True,
    requires_restart=True,
    available_setting_description="IPv6 support",
    help_description="Enable or disable IPv6 support.",
    value_to_help={
        "off": "Disable IPv6 (default)",
        "on": " Enable IPv6"
    },
    help_epilog="""\b
Values:
{feature_values}
\b
Examples:
  {program_name} {config_command} {set_command} {feature_command} on
  {program_name} {config_command} {set_command} {feature_command} off
\b
Current Setting:
  Run '{program_name} {config_command} {settings_list_command}' to see current value.
\b
How It Works:
  When enabled, IPv6 traffic will be routed through the VPN tunnel.""",
    click_type=ToggleType()
)


ANON_CRASH_REPORTS_FEATURE = ClickFeature(
    command="anonymous-crash-reports",
    human_friendly_name="Anonymous crash reports",
    setting_path="anonymous_crash_reports",
    available_on_free_tier=True,
    available_setting_description="Anonymous crash reporting",
    help_description="Enable or disable anonymous crash reports.",
    value_to_help={
        "off": "Disable crash reporting",
        "on": " Enable anonymous crash reporting"
    },
    help_epilog="""\b
Values:
{feature_values}
\b
Examples:
  {program_name} {config_command} {set_command} {feature_command} on
  {program_name} {config_command} {set_command} {feature_command} off
\b
Current Setting:
  Run '{program_name} {config_command} {settings_list_command}' to see current value.
\b
How It Works:
  When enabled, the CLI sends anonymous crash reports to help us:
  - Fix bugs and improve stability
  - Detect firewall interference
  - Avoid VPN blocks
\b
Privacy:
  - Reports are completely anonymous
  - No personal information is collected
  - Helps improve the CLI for everyone""",
    click_type=ToggleType()
)


PORT_FORWARDING_FEATURE = ClickFeature(
    command="port-forwarding",
    human_friendly_name="Port forwarding",
    setting_path="features.port_forwarding",
    available_setting_description="Enable port forwarding for P2P",
    help_description="Enable or disable port forwarding for P2P applications.",
    value_to_help={
        "off": "Disable port forwarding",
        "on": " Enable port forwarding"
    },
    help_epilog="""\b
Values:
{feature_values}
\b
How It Works:
  When enabled, the VPN client requests a forwarded port during
  connection to P2P-capable servers. The port assignment requires
  an external script to maintain the lease and retrieve the port
  number. Without the script, the assigned port expires.
\b
Setup Guide:
  https://protonvpn.com/support/port-forwarding-manual-setup#linux
\b
Examples:
  {program_name} {config_command} {set_command} {feature_command} on
  {program_name} {config_command} {set_command} {feature_command} off""",
    click_type=ToggleType()
)


CUSTOM_DNS_FEATURE = ClickFeature(
    command="custom-dns",
    human_friendly_name="Custom DNS",
    setting_path="custom_dns",
    requires_restart=True,
    available_setting_description="Use custom DNS servers",
    help_description="Configure custom DNS servers.",
    value_to_help={
        "off": "Disable custom DNS (use Proton's DNS)",
        "on": " Enable custom DNS with specified servers"
    },
    help_epilog="""\b
Values:
{feature_values}
\b
Examples:
  # Enable with custom DNS
  {program_name} {config_command} {set_command} {feature_command} on --dns 1.1.1.1,8.8.8.8
\b
  # Enable with IPv6
  {program_name} {config_command} {set_command} {feature_command} on --dns 2606:4700:4700::1111
\b
  # Disable custom DNS
  {program_name} {config_command} {set_command} {feature_command} off
\b
Current Setting:
  Run '{program_name} {config_command} {settings_list_command}' to see current DNS configuration.
""",
    click_type=CustomDNSType(),
)


NETSHIELD_FEATURE = ClickFeature(
    command="netshield",
    human_friendly_name="NetShield",
    setting_path="features.netshield",
    available_setting_description="Ad-blocking and malware protection",
    help_description="Configure NetShield ad-blocking and malware protection.",
    value_to_help={
        "off": "                 NetShield disabled",
        "malware-only": "        Block malware domains",
        "malware-ads-trackers": "Block malware, ads, and trackers (recommended)"
    },
    help_epilog="""\b
Values:
{feature_values}
\b
Examples:
  {program_name} {config_command} {set_command} {feature_command} off
  {program_name} {config_command} {set_command} {feature_command} malware-only
  {program_name} {config_command} {set_command} {feature_command} malware-ads-trackers
\b
Current Setting:
  Run '{program_name} {config_command} {settings_list_command}' to see current value.
\b
How It Works:
  NetShield blocks malicious and advertising domains at the DNS level,
  preventing malware downloads and removing ads before they load.""",
    click_type=NetshieldType()
)


KILLSWITCH_FEATURE = ClickFeature(
    command="kill-switch",
    human_friendly_name="Kill switch",
    setting_path="killswitch",
    available_on_free_tier=True,
    available_setting_description="Block internet if VPN drops",
    help_description="Configure Kill Switch to block internet if VPN connection drops.",
    value_to_help={
        "off": "     Disable Kill Switch (internet always accessible)",
        "standard": "Block internet only while VPN is active"
    },
    help_epilog="""\b
Values:
{feature_values}
\b
Examples:
  {program_name} {config_command} {set_command} {feature_command} off
  {program_name} {config_command} {set_command} {feature_command} standard
\b
Current Setting:
  Run '{program_name} {config_command} {settings_list_command}' to see current value.
\b
Behavior:
  - standard: Blocks internet if VPN drops during active connection
              Restores internet when you disconnect intentionally""",
    click_type=KillSwitchType()
)

PROTOCOL_FEATURE = ClickFeature(
    command="protocol",
    human_friendly_name="Protocol",
    setting_path="protocol",
    available_on_free_tier=True,
    available_setting_description="Protocol used to establish the tunnel",
    help_description="Select the protocol used to establish the VPN tunnel.",
    value_to_help={
        WIREGUARD: "   WireGuard over UDP (default, recommended)",
        OPENVPN_UDP: " OpenVPN over UDP",
        OPENVPN_TCP: " OpenVPN over TCP (works where UDP is blocked)",
    },
    help_epilog="""\b
Values:
{feature_values}
\b
Examples:
  {program_name} {config_command} {set_command} {feature_command} wireguard
  {program_name} {config_command} {set_command} {feature_command} openvpn-tcp
\b
Current Setting:
  Run '{program_name} {config_command} {settings_list_command}' to see current value.
\b
How It Works:
  WireGuard over UDP is the fastest option and is used by default.
\b
  Some networks (public hotspots, hotels, corporate WiFi) drop the UDP
  traffic that WireGuard and OpenVPN/UDP rely on. The tunnel is created
  but the handshake never gets a reply, so the connection times out. On
  such a network, openvpn-tcp establishes the tunnel over TCP instead
  and connects normally.
\b
Recommendation:
  Keep wireguard unless you are on a network that blocks UDP.""",
    click_type=ProtocolType()
)


BOOL_FEATURES = [
    VPN_ACCELERATOR_FEATURE,
    MODERATE_NAT_FEATURE,
    IPV6_FEATURE,
    ANON_CRASH_REPORTS_FEATURE,
    PORT_FORWARDING_FEATURE,
]

ALL_FEATURES = [
    PROTOCOL_FEATURE,
    NETSHIELD_FEATURE,
    KILLSWITCH_FEATURE,
    PORT_FORWARDING_FEATURE,
    CUSTOM_DNS_FEATURE,
    VPN_ACCELERATOR_FEATURE,
    MODERATE_NAT_FEATURE,
    IPV6_FEATURE,
    ANON_CRASH_REPORTS_FEATURE,
]
