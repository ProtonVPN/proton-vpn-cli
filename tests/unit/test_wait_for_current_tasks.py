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
import pytest

from proton.vpn.cli.core.wait_for_current_tasks import wait_for_current_tasks


@pytest.mark.asyncio
async def test_wait_for_current_tasks_waits_for_other_tasks():
    done = []

    async def work():
        await asyncio.sleep(0)
        done.append(True)

    asyncio.create_task(work())
    await wait_for_current_tasks()

    assert done == [True]


@pytest.mark.asyncio
async def test_wait_for_current_tasks_ignores_tasks_cancelled_while_waiting():
    task = asyncio.create_task(asyncio.sleep(10))
    asyncio.get_running_loop().call_later(0.01, task.cancel)

    await wait_for_current_tasks()

    assert task.cancelled()


@pytest.mark.asyncio
async def test_wait_for_current_tasks_ignores_tasks_that_fail():
    async def fail():
        raise RuntimeError("failed")

    task = asyncio.create_task(fail())
    await wait_for_current_tasks()

    assert isinstance(task.exception(), RuntimeError)
