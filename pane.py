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
        return View(UItem('selected_device', style='custom'))


class DevicaTabularAdapter(TabularAdapter):
    columns = [('Name', 'name')]


class DevicesPane(TraitsDockPane):

    id = 'plv.devices'
    def traits_view(self):
        return View(UItem('devices', editor=TabularEditor(selected='selected_device',
                                                          adapter=DevicaTabularAdapter())))
# ============= EOF =============================================
