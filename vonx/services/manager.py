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
import logging
import multiprocessing as mp
import os
from typing import Mapping

from .base import ServiceBase
from . import exchange as exch

LOGGER = logging.getLogger(__name__)


class ServiceManager:
    def __init__(self, env: Mapping = None):
        self._env = env or {}
        self._exchange = exch.Exchange()
        self._executor_cls = exch.RequestExecutor
        self._proc_locals = {'pid': os.getpid()}
        self._process = None
        self._services = {}
        self._services_cfg = None
        self._init_services()

    def _init_services(self) -> None:
        """
        Initialize all dependent services
        """
        pass

    def add_service(self, svc_id: str, service: ServiceBase):
        """
        Add a service to the service manager instance

        Args:
            svc_id: the unique identifier for the service
            service: the service instance
        """
        self._services[svc_id] = service

    def start(self) -> None:
        """
        Start the message processor and any other services
        """
        asyncio.get_child_watcher()
        self._process = mp.Process(target=self._start)
        self._process.start()

    def _start(self, wait: bool = True) -> None:
        """
        Run loop for the main process
        """
        self._init_process()
        self._exchange.start()
        self._start_services(wait)
        self._exchange.join()

    def _init_process(self) -> None:
        """
        Initialize ourselves in a newly started process
        """
        # create new event loop after fork
        asyncio.get_event_loop().close()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    def _start_services(self, wait: bool = True) -> None:
        """
        Start all registered services
        """
        for svc_id, service in self._services.items():
            service.start(wait)

    def stop(self, wait: bool = True) -> None:
        """
        Stop the message processor and any other services
        """
        self._stop_services(wait)
        self._exchange.stop()

    def _stop_services(self, wait: bool = True) -> None:
        """
        Stop all registered services
        """
        for _id, service in self._services.items():
            service.stop(wait)

    @property
    def env(self) -> dict:
        """
        Accessor for our local environment dict
        """
        return self._env

    @property
    def exchange(self) -> exch.Exchange:
        """
        Accessor for the Exchange this ServiceManager uses for messaging
        """
        return self._exchange

    @property
    def proc_locals(self) -> dict:
        """
        Accessor for all process-local variables

        Returns:
            a dictionary of currently-defined variables
        """
        pid = os.getpid()
        if self._proc_locals['pid'] != pid:
            self._proc_locals = {'pid': pid}
        return self._proc_locals

    @property
    def executor(self) -> exch.RequestExecutor:
        """
        Return a per-process request executor which manages requests
        and polls for results coming from other services.
        Note: this is called for each worker process started by the webserver.
        """
        ploc = self.proc_locals
        if not 'executor' in ploc:
            ident = 'exec-{}'.format(ploc['pid'])
            ploc['executor'] = self._executor_cls(ident, self._exchange)
            ploc['executor'].start()
        return ploc['executor']

    def get_service(self, name: str):
        """
        Fetch a defined service by name

        Args:
            name: the string identifier for the service

        Returns:
            the service instance, or None if not found
        """
        return self._services.get(name)

    def get_message_target(self, name: str) -> exch.MessageTarget:
        """
        Get an endpoint for one of the services defined by this manager.
        This Endpoint can be used for sending process-safe messages and receiving results.

        Args:
            name: the string identifier for the service
            loop: the current event loop, if any
        """
        if name in self._services:
            return self.executor.get_message_target(self._services[name].pid)
        return None

    def get_request_target(self, name: str) -> exch.RequestTarget:
        """
        Get an endpoint for sending messages to a service on the message exchange.
        Requests will be handled by the executor for this manager in this process.

        Args:
            name: the string identifier for the service
            loop: the current event loop, if any
        """
        ploc = self.proc_locals
        tg_name = 'target_' + name
        if tg_name not in ploc:
            if name in self._services:
                pid = self._services[name].pid
                ploc[tg_name] = self.executor.get_request_target(pid)
            else:
                return None
        return ploc[tg_name]
