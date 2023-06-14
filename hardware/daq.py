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
from hardware.adc import Channel
from hardware.device import Device
from traits.api import List


class DAQ(Device):
    channels = List(Channel)

    def load(self, cfg):
        self.channels = [Channel(**ci) for ci in cfg["channels"]]

    def get_value(self, idx=0, datastream="default"):
        ch = self.channels[idx]
        v = self.driver.read_channel(ch.address)
        vv = ch.map_value(v)
        self.debug(f"get value volts={v}, value={vv}")

        self.update = {"datastream": datastream, "value": vv}
        return vv


class USBTemp(DAQ):
    pass


# ============= EOF =============================================
