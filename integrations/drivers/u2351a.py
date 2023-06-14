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
from hardware.driver.driver import Driver
from integrations.drivers.base import BaseSwitchDriver
from loggable import Loggable


class U2351A(BaseSwitchDriver):
    write_terminator = "\n"

    def load(self, cfg):
        self.ask("*IDN?")

    def _actuate_channel(self, channel, v):
        if isinstance(v, bool):
            v = 10 if v else 0
        self.set_voltage(channel, v)

    def set_voltage(self, channel, output):
        current_voltage = self.get_voltage(channel)
        self.debug(f"current voltage {current_voltage}")

        msg = f"SOUR:VOLT {output:0.3f}, (@{channel})"
        self.ask(msg)

    def get_voltage(self, channel):
        msg = f"SOUR:VOLT? (@{channel})"
        resp = self.ask(msg)
        return float(resp)


# ============= EOF =============================================
