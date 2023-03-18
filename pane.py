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
from pyface.tasks.traits_dock_pane import TraitsDockPane
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traitsui.api import View, Item, UItem
from traitsui.editors import TabularEditor
from traitsui.tabular_adapter import TabularAdapter


class HardwareCentralPane(TraitsTaskPane):
    def traits_view(self):
        return View(UItem('selection', style='custom'))


class DeviceTabularAdapter(TabularAdapter):
    columns = [('Name', 'name')]


class DashboardTabularAdapter(TabularAdapter):
    columns = [('Name', 'name')]


class AutomationTabularAdapter(TabularAdapter):
    columns = [('Name', 'name')]


class DevicesPane(TraitsDockPane):
    id = 'laba.devices'
    name = 'Devices'

    def traits_view(self):
        return View(UItem('devices', editor=TabularEditor(selected='selection',
                                                          adapter=DeviceTabularAdapter())))


class DashboardsPane(TraitsDockPane):
    id = 'laba.dashboards'
    name = 'Dashboards'

    def traits_view(self):
        return View(UItem('dashboards', editor=TabularEditor(selected='selection',
                                                             adapter=DashboardTabularAdapter())))


class AutomationsPane(TraitsDockPane):
    id = 'laba.automations'
    name = 'Automations'

    def traits_view(self):
        return View(UItem('automations', editor=TabularEditor(selected='selection',
                                                              adapter=AutomationTabularAdapter())))

# ============= EOF =============================================
