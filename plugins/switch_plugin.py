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
from hardware.device import Device
from plugin import BasePlugin
from traits.api import List


class SwitchPlugin(BasePlugin):
    id = 'laba.plugin.switch'
    automation_commands = List(contributes_to='laba.automation.commands')

    def _automation_commands_default(self):
        return [('open_switch', self.open_switch),
                ('close_switch', self.close_switch)]

    def open_switch(self, name, *args, **kw):
        self._actuate_switch(name, True, *args, **kw)

    def close_switch(self, name, *args, **kw):
        self._actuate_switch(name, False, *args, **kw)

    def _actuate_switch(self, name, state, *args, **kw):
        for sw in self.application.get_services(Device):
            if not hasattr(sw, 'switches'):
                continue

            for si in sw.switches:
                if si.name == name:
                    func = sw.open_switch if state else sw.close_switch
                    func(name, *args, **kw)
                    break

# ============= EOF =============================================
