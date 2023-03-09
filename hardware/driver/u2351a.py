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
from loggable import Loggable


class U2351A(Driver):
    def actuate_channel(self, channel, state):
        v = 10 if state else 0
        msg = f"SOUR:VOLT {v},(@{channel})"
        self.ask(msg)

    def set_voltage(self, channel, output):
        msg = f"SOUR:VOLT {output:0.3f}, (@{channel})"
        self.ask(msg)

    def ask(self, *args, **kw):
        self.communicator.ask(*args, **kw)
# ============= EOF =============================================
