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

from hardware.communicator import Communicator


class SerialCommunicator(Communicator):
    def open(self):
        try:
            self.handle = serial.Serial(
                self.configobj.get("port", "COM1"),
                parity=self.configobj.get("parity", "N"),
                stopbits=self.configobj.get("stopbits", 1),
                bytesize=self.configobj.get("bytesize", 8),
                baudrate=self.configobj.get("baudrate", 9600),
                timeout=self.configobj.get("timeout", 1),
            )

            return True
        except serial.SerialException as e:
            self.warning(f"Failed opening serial port {e}")
            return

    def _ask(self, msg, *args, **kw):
        if self.handle:
            if isinstance(msg, str):
                msg = msg.encode("utf-8")

            self.handle.write(msg)
            return self.handle.readline()


# ============= EOF =============================================
