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
from integrations.drivers.base import BaseDAQDriver


class USBTemp(BaseDAQDriver):
    # def initialize(self, *args, **kw):
    #     super().initialize(*args, **kw)
    #
    #     # configure dio channels
    #     for i in range(4):
    #         self.communicator.d_config(i, 0, port="AUXPORT")

    def configure_input(self, channel):
        self.communicator.configure_input(channel, port="AUXPORT")

    def configure_output(self, channel):
        self.communicator.configure_output(channel, port="AUXPORT")

    def actuate_channel(self, channel, state):
        self.communicator.d_out(channel, state, port="AUXPORT")

    def _read_channel(self, channel):
        return self.communicator.a_in(channel)

    def _read_temperature(self, channel):
        return self.communicator.t_in(channel)


# ============= EOF =============================================
