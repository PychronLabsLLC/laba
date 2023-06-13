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
from hardware.device import Device


class Gauge(Device):
    def scan_pressure(self, *args, **kw):
        pressure = self.driver.read_pressure(args[0])
        self.debug(f"scan pressure {pressure}, {type(pressure)})")
        return pressure


# ============= EOF =============================================
