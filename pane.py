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
from traitsui.api import View, Item, UItem, VGroup, HGroup, spring
from traitsui.editors import TabularEditor
from traitsui.tabular_adapter import TabularAdapter

from util import icon_button_editor


class SequenceEditorPane(TraitsDockPane):
    name = 'Editor'
    id = 'laba.sequencer.editor'

    def traits_view(self):
        return View(icon_button_editor('add_button', 'add'),
                    icon_button_editor('save_button', 'save'))


class SequenceAdapter(TabularAdapter):
    columns = [('Name', 'name')]

    def _get_bg_color(self):
        if self.item.state == 'not run':
            color = 'gray'
        elif self.item.state == 'running':
            color = 'lightyellow'
        elif self.item.state == 'success':
            color = 'green'
        elif self.item.state == 'failed':
            color = 'gray'
        return color

    def _get_text_color(self):
        color = 'white'
        # if self.item.state == 'not run':
        #     color = 'gray'
        if self.item.state == 'running':
            color = 'black'
        # elif self.item.state == 'success':
        #     color = 'green'
        # elif self.item.state == 'failed':
        #     color = 'gray'
        return color


class SequenceStepAdapter(TabularAdapter):
    columns = [('Name', 'name')]


class SequenceControlPane(TraitsDockPane):
    id = 'laba.sequencer.controls'
    name = 'Controls'

    movable = False
    closable = False
    floatable = False

    def traits_view(self):
        v = View(HGroup(icon_button_editor('start_button', 'start'),
                        spring,
                        UItem('object.sequencer.timer', style='custom')
                        # UItem('pause_button'),
                        # UItem('continue_button'),
                        ))
        return v


class SequenceCentralPane(TraitsTaskPane):
    def traits_view(self):
        v = View(VGroup(UItem('object.sequencer.sequences',
                              editor=TabularEditor(selected='object.sequencer.selected',
                                                   auto_update=True,
                                                   editable=False,
                                                   adapter=SequenceAdapter())),

                        UItem('object.sequencer.selected.steps',
                              editor=TabularEditor(selected='selected_step',
                                                   adapter=SequenceStepAdapter()))
                        # UItem('object.sequencer.selected', style='custom')

                        )
                 )
        return v


class ConsolePane(TraitsDockPane):
    name = 'Console'
    id = 'laba.console'

    def traits_view(self):

        return View(
            UItem('console', style='custom')
        )


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
