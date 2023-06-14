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
from hardware.util import get_float
from hardware.driver.driver import Driver


class BaseADCDriver(Driver):
    @get_float()
    def read_channel(self, channel):
        self.debug(f"read channel {channel}")
        return self._read_channel(channel)

    def _read_channel(self, channel):
        raise NotImplementedError


class BaseDAQDriver(BaseADCDriver):
    pass


class BaseDACDriver(Driver):
    def write_channel(self, channel, value):
        self.debug(f"write channel {channel} value={value}")
        self._write_channel(channel, value)

    def _write_channel(self, channel, value):
        raise NotImplementedError


class BaseSwitchDriver(Driver):
    def actuate_channel(self, channel, state):
        self.debug(f"actuate channel {channel} {state}")
        return self._actuate_channel(channel, state)

    def _actuate_channel(self, channel, state):
        raise NotImplementedError


class BasePressureDriver(Driver):
    @get_float()
    def read_pressure(self, channel):
        self.debug(f"read pressure channel={channel}")
        return self._read_pressure(channel)

    def _read_pressure(self, channel):
        raise NotImplementedError


# ============= EOF =============================================
