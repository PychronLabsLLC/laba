# ===============================================================================
# Copyright 2023 ross
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
# ===============================================================================

from threading import Thread, Event
from traits.api import Any, Int

import zmq

from hardware.device import Device
from loggable import Loggable


class Server(Loggable):
    _thread = None
    application = Any
    port = Int

    def run(self):
        self._thread = Thread(target=self._run)
        self._thread.start()

    def _run(self):
        """

        API.

        {
            "device": <name of a device>,
            "function": <name of the function>
            "kwargs": <keyward arguments to pass into the function when its is called>
        }

        :returns
        {
            "message": ...
            "response": ...
        }

        """

        self.debug(f'Starting server. {self.port}')

        context = zmq.Context()
        socket = context.socket(zmq.REP)

        socket.bind(f"tcp://*:{self.port}")
        self._active = Event()
        while not self._active.is_set():
            message = socket.recv_json()
            self.debug(f"Received request: {message}")

            device_name = message.get('device')
            reply = {"message": "no device"}
            if device_name:
                func_name = message.get('function')
                reply = {"message": "no function"}
                if func_name:
                    reply = {"message": f"invalid device={device_name}"}
                    dev = self.application.get_service(Device, f"name=='{device_name}'")
                    if dev:
                        try:
                            func = getattr(dev, func_name)
                            kwargs = message.get('kwargs', {})
                            reply = {"message": "OK", "response": func(**kwargs)}
                        except AttributeError:
                            reply = {"message": f"invalid function={func_name}"}

            # Send reply back to client
            socket.send_json(reply)

# ============= EOF =============================================
