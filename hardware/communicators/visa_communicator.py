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
import pyvisa

resource_manager = pyvisa.ResourceManager()

from hardware.communicator import Communicator


class VisaCommunicator(Communicator):
    def open(self):
        self.debug("opening visa usb communicator")
        self.debug("======= Visa Resources =======")
        for r in resource_manager.list_resources():
            self.debug(f"    {r}")
        self.debug("==============================")

        address = self._make_address()

        self.handle = resource_manager.open_resource(
            address, write_termination=self.config('write_terminator', '\n'),
            read_termination=self.config('read_terminator', '\n')
        )

        if self.handle is not None:
            return True

    def _make_address(self):
        address = self.config("address")
        if address:
            return address

        b = self.config("board", 0)
        m = self.config("manufacture_id", 0)
        mc = self.config("model_code", 0)
        sn = self.config("serial_number", 0)

        base = f"USB{b}::{m}::{mc}::{sn}"
        uin = self.config("usb_interface_number")
        if uin:
            base = f"{base}::{uin}"

        return f"{base}::INSTR"

    def _tell(self, *args, **kw):
        if self.handle:
            try:
                return self.handle.write(*args, **kw)
            except pyvisa.errors.VisaIOError as e:
                self.debug(f"tell error {args}, {kw}")
                self.debug_exception()

    def _ask(self, *args, **kw):
        if self.handle:
            try:
                return self.handle.query(*args, **kw)
            except pyvisa.errors.VisaIOError as e:
                self.debug(f"ask error {args}, {kw}")
                self.debug_exception()

# ============= EOF =============================================
