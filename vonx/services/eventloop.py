#
# Copyright 2017-2018 Government of Canada
# Public Services and Procurement Canada - buyandsell.gc.ca
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import asyncio
from concurrent.futures import Future
from types import CoroutineType
import logging

LOGGER = logging.getLogger(__name__)


def run_coro(coro: CoroutineType):
    """
    Run an async coroutine and wait for the results

    Args:
        coro (CoroutineType): The coroutine to execute
    Returns:
        The result of the coroutine
    """
    event_loop = None
    try:
        event_loop = asyncio.get_event_loop()
    except RuntimeError:
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
    return event_loop.run_until_complete(coro)


def run_in_executor(executor, coro: CoroutineType) -> Future:
    """
    Run an async coroutine in an executor when we aren't already inside an event loop

    Args:
        executor: A `ThreadExecutor` or `ProcessExecutor` instance which will run the coroutine
    Returns:
        A `Future` which can be used to access the result of the coroutine
    """
    loop = asyncio.new_event_loop()
    def run_sync_loop(loop, coro):
        asyncio.set_event_loop(loop)
        loop.run_until_complete(coro)
    future = executor.submit(run_sync_loop, loop, coro)
    return future


async def ensure_future(coro):
    """
    Wrap coroutine in a future to ensure that unhandled exceptions are logged
    """
    fut = asyncio.ensure_future(coro)
    return fut.result()