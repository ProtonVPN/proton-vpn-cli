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
from unittest.mock import AsyncMock, Mock, PropertyMock
import pytest

from click.core import Context as ClickContext

from proton.vpn.cli.core.controller import Controller, Params, Feature
from proton.vpn.cli.core.exceptions import \
    AuthenticationRequiredError, \
    RequiresHigherTierError
from proton.vpn.connection import states
from proton.vpn.core.api import ProtonVPNAPI, VPNDataRefresher, Settings
from proton.vpn.core.vpnconnector import VPNConnector
from proton.vpn.session.servers.types import LogicalServer, ServerFeatureEnum


@pytest.mark.asyncio
async def test_connect_fails_if_not_logged_in():
    api_mock = Mock()
    params_mock = Mock()
    click_ctx_mock = Mock()
    server = Mock()

    api_mock.is_user_logged_in.return_value = False
    controller = Controller(params_mock, click_ctx_mock, api_mock)
    with pytest.raises(AuthenticationRequiredError):
        await controller.connect(server)


@pytest.mark.asyncio
async def test_find_logical_server_fails_if_not_logged_in():
    api_mock = Mock()
    params_mock = Mock()
    click_ctx_mock = Mock()

    api_mock.is_user_logged_in.return_value = False
    controller = Controller(params_mock, click_ctx_mock, api_mock)
    with pytest.raises(AuthenticationRequiredError):
        await controller.find_logical_server()


@pytest.mark.asyncio
async def test_find_logical_server_fails_when_specifying_server_name_as_free_user():
    api_mock = Mock()
    params_mock = Mock()
    click_ctx_mock = Mock()

    # mock free user tier
    user_tier_property = PropertyMock(return_value=0)
    type(api_mock).user_tier = user_tier_property

    controller = Controller(params_mock, click_ctx_mock, api_mock)
    with pytest.raises(RequiresHigherTierError):
        await controller.find_logical_server(server_name="name")


@pytest.mark.asyncio
async def test_find_logical_server_fails_when_specifying_country_as_free_user():
    api_mock = Mock()
    params_mock = Mock()
    click_ctx_mock = Mock()

    # mock free user tier
    user_tier_property = PropertyMock(return_value=0)
    type(api_mock).user_tier = user_tier_property

    controller = Controller(params_mock, click_ctx_mock, api_mock)
    with pytest.raises(RequiresHigherTierError):
        await controller.find_logical_server(country="FR")


@pytest.mark.asyncio
async def test_find_logical_server_fails_when_specifying_city_as_free_user():
    api_mock = Mock()
    params_mock = Mock()
    click_ctx_mock = Mock()

    # mock free user tier
    user_tier_property = PropertyMock(return_value=0)
    type(api_mock).user_tier = user_tier_property

    controller = Controller(params_mock, click_ctx_mock, api_mock)
    with pytest.raises(RequiresHigherTierError):
        await controller.find_logical_server(city="Milan")


@pytest.mark.asyncio
async def test_find_logical_server_fails_when_requesting_features_as_free_user():
    api_mock = Mock()
    params_mock = Mock()
    click_ctx_mock = Mock()

    # mock free user tier
    user_tier_property = PropertyMock(return_value=0)
    type(api_mock).user_tier = user_tier_property

    controller = Controller(params_mock, click_ctx_mock, api_mock)
    with pytest.raises(RequiresHigherTierError):
        await controller.find_logical_server(features=ServerFeatureEnum.P2P)


@pytest.mark.asyncio
async def test_find_logical_server_fails_when_requesting_random_server_as_free_user():
    api_mock = Mock()
    params_mock = Mock()
    click_ctx_mock = Mock()

    # mock free user tier
    user_tier_property = PropertyMock(return_value=0)
    type(api_mock).user_tier = user_tier_property

    controller = Controller(params_mock, click_ctx_mock, api_mock)
    with pytest.raises(RequiresHigherTierError):
        await controller.find_logical_server(random_server=True)


@pytest.mark.asyncio
async def test_connect_disconnects_when_connection_fails():
    api_mock = AsyncMock(spec=ProtonVPNAPI)
    api_mock.refresher = AsyncMock(spec=VPNDataRefresher)
    params_mock = Mock(spec=Params)
    click_ctx_mock = Mock(spec=ClickContext)
    vpn_connector_mock = Mock(spec=VPNConnector)
    server = Mock(spec=LogicalServer)

    # mock inactive connection
    vpn_connector_mock.is_connection_active = False
    api_mock.get_vpn_connector.return_value = vpn_connector_mock

    # grab subscribers to connection events and
    # send them an Error event to simulate connection failure
    # followed by a Disconnected event to indicate end of disconnection
    def notify_event(subscriber):
        if not notify_event.error_sent:
            # first we let the controller know the connection failed
            subscriber.status_update(states.Error())
            notify_event.error_sent = True
        else:
            # then we let it know the "disconnection" has completed
            subscriber.status_update(states.Disconnected)
    notify_event.error_sent = False
    vpn_connector_mock.register.side_effect = notify_event

    controller = Controller(params_mock, click_ctx_mock, api_mock)
    await controller.connect(server)
    vpn_connector_mock.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_get_all_countries_raises_authentication_required_exception_when_user_is_not_logged_in():
    api_mock = AsyncMock(spec=ProtonVPNAPI)
    api_mock.is_user_logged_in.return_value = False
    params_mock = Mock(spec=Params)
    click_ctx_mock = Mock(spec=ClickContext)
    controller = Controller(params_mock, click_ctx_mock, api_mock)

    with pytest.raises(AuthenticationRequiredError):
        await controller.get_all_countries()


@pytest.mark.asyncio
async def test_save_feature_setting_raises_exception_when_not_signed_in():
    api_mock = AsyncMock(spec=ProtonVPNAPI)
    api_mock.is_user_logged_in.return_value = False
    params_mock = Mock(spec=Params)
    click_ctx_mock = Mock(spec=ClickContext)
    controller = Controller(params_mock, click_ctx_mock, api_mock)

    with pytest.raises(AuthenticationRequiredError):
        await controller.save_feature_setting(Mock(), Mock())


@pytest.mark.asyncio
async def test_save_feature_setting_raises_exception_when_feature_requires_higher_tier():
    api_mock = AsyncMock(spec=ProtonVPNAPI)
    api_mock.is_user_logged_in.return_value = True
    api_mock.user_tier = 0  # Free tier
    params_mock = Mock(spec=Params)
    click_ctx_mock = Mock(spec=ClickContext)
    controller = Controller(params_mock, click_ctx_mock, api_mock)
    feature_mock = Mock(spec=Feature)
    feature_mock.available_on_free_tier = False

    with pytest.raises(RequiresHigherTierError):
        await controller.save_feature_setting(feature_mock, Mock())


@pytest.mark.asyncio
async def test_get_feature_setting_raises_exception_when_not_signed_in():
    api_mock = AsyncMock(spec=ProtonVPNAPI)
    api_mock.is_user_logged_in.return_value = False
    params_mock = Mock(spec=Params)
    click_ctx_mock = Mock(spec=ClickContext)
    controller = Controller(params_mock, click_ctx_mock, api_mock)

    with pytest.raises(AuthenticationRequiredError):
        await controller.get_feature_setting(Mock())


@pytest.mark.asyncio
async def test_save_settings_waits_for_confirmation_when_requesting_paying_connection_features():
    api_mock = AsyncMock(spec=ProtonVPNAPI)
    params_mock = Mock(spec=Params)
    click_ctx_mock = Mock(spec=ClickContext)
    vpn_connector_mock = Mock(spec=VPNConnector)
    settings = Settings.default(user_tier=1)

    # mock paying user
    api_mock.user_tier = 1

    # mock active connection
    vpn_connector_mock.is_connected = True
    api_mock.get_vpn_connector.return_value = vpn_connector_mock

    # mock Connection event confirmation after features request
    def notify_event(subscriber):
        subscriber.status_update(states.Connected)
    vpn_connector_mock.register.side_effect = notify_event

    controller = Controller(params_mock, click_ctx_mock, api_mock)
    await controller.save_settings(settings)

    # check that a Connection event listener was registered
    vpn_connector_mock.register.assert_called_once()
    api_mock.save_settings.assert_called_with(settings)


@pytest.mark.asyncio
async def test_save_settings_does_not_wait_for_confirmation_when_requesting_free_connection_features():
    api_mock = AsyncMock(spec=ProtonVPNAPI)
    params_mock = Mock(spec=Params)
    click_ctx_mock = Mock(spec=ClickContext)
    vpn_connector_mock = Mock(spec=VPNConnector)
    settings = Settings.default(user_tier=0)

    # mock free user
    api_mock.user_tier = 0

    # mock active connection
    vpn_connector_mock.is_connected = True
    api_mock.get_vpn_connector.return_value = vpn_connector_mock

    controller = Controller(params_mock, click_ctx_mock, api_mock)
    await controller.save_settings(settings)

    # check that a Connection event listener was not registered
    vpn_connector_mock.register.assert_not_called()
    api_mock.save_settings.assert_called_with(settings)
