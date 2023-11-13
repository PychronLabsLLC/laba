# ===============================================================================
# Copyright 2023 Jake Ross
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
from hardware.util import get_float
from integrations.drivers.base import BaseSwitchDriver


class SCM9B3182(BaseSwitchDriver):
    use_handshake = True

    def load(self, cfg):
        self.use_handshake = cfg.get("use_handshake", True)

    def _actuate_channel(self, channel, v):
        if isinstance(v, bool):
            v = self.config("max_voltage", 10) if v else self.config("min_voltage", 0)
        self.set_voltage(channel, v)

    def set_voltage(self, channel, volts):
        # current_voltage = self.get_voltage(channel)
        # self.debug(f"current voltage {current_voltage}")
        #
        # msg = f"SOUR:VOLT {output:0.3f}, (@{channel})"
        # self.tell(msg)

        if self.use_handshake:
            prompt = "#"
        else:
            prompt = "$"

        output = volts * 1000
        resp = self.ask(f"{prompt}1AO+{output:08.2f}")
        if self.use_handshake and resp:
            """
            example handshake response
             *1AO+00010.0095
            """
            if resp[0] != "*":
                self.warning(f"Error setting voltage. resp={resp}")
                return

            if "+" in resp:
                resp = resp.split("+")[1]
                resp = resp[:-3]  # trim off checksum
                if float(resp) != output:
                    self.warning(f"Error setting voltage to {output}mV. resp={resp}")
                    return

            resp = self.ask("$1ACK")
            if resp.strip() != "*":
                self.warning(f"Error setting voltage. resp={resp}")

    @get_float()
    def get_voltage(self, channel):
        return self.ask("$1RD")
        # msg = f"SOUR:VOLT? (@{channel})"
        # resp = self.ask(msg)
        # if resp is not None:
        #     return float(resp)


# ============= EOF =============================================
