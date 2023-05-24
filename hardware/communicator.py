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
import serial

from loggable import Loggable


class Communicator(Loggable):
    handle = None
    simulation = True

    def open(self):
        pass

    def ask(self, msg, *args, **kw):
        resp = self._ask(msg, *args, **kw)
        self.debug(f"{msg}=>{resp}")
        return resp

    def _ask(self, *args, **kw):
        raise NotImplementedError

    def bootstrap(self):
        try:
            if self.open():
                self.simulation = False
        except BaseException:
            self.debug(f'failed bootstrap {self}')
            self.debug_exception()


class SerialCommunicator(Communicator):
    def open(self):
        try:
            self.handle = serial.Serial(self.configobj.get("port", "COM1"))
            return True
        except serial.SerialException as e:
            self.warning(f"Failed opening serial port {e}")
            return

    def _ask(self, msg, *args, **kw):
        if self.handle:
            self.handle.write(msg)
            return self.handle.read()


class EthernetCommunicator(Communicator):
    def _ask(self, *args, **kw):
        pass


class TelnetCommunicator(Communicator):
    pass


class TCPCommunicator(EthernetCommunicator):
    pass


class UDPCommunicator(EthernetCommunicator):
    pass


class ZmqCommunicator(Communicator):
    pass


# ============= EOF =============================================
