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
from traitsui.editors import TabularEditor, InstanceEditor, EnumEditor
from traitsui.tabular_adapter import TabularAdapter
from traits.api import HasTraits, List, Instance, Button, Str, Any, on_trait_change, Property, cached_property

from util import icon_button_editor

edit_view = View(
    VGroup(Item('name'),
           HGroup(VGroup(UItem('steps'),
                         show_border=True,
                         label='Steps')
                  )
           )
)


class SequenceEditorPane(TraitsDockPane):
    name = 'Editor'
    id = 'laba.sequencer.editor'

    def traits_view(self):
        return View(VGroup(

                           icon_button_editor('save_button', 'save'),
                           HGroup(UItem('object.sequencer.sequence_template',
                                        editor=EnumEditor(name='object.sequencer.available_sequence_templates')),
                                  icon_button_editor('add_button', 'add')),
                           icon_button_editor('add_step_button', 'load'),
                           UItem('add_automation_button'),
                           Item('object.sequencer.edit_name'),
                           )
                    )


class SequenceAdapter(TabularAdapter):
    columns = [('Name', 'name'), ('Steps', 'steps'), ('State', 'state')]
    state_text = Property
    steps_text = Property

    def _get_state_text(self):
        return self.item.state

    def _get_steps_text(self):
        return f'{len(self.item.steps)}'

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
    columns = [('Name', 'name'), ('Automations', 'automations')]
    automations_text = Property

    def _get_automations_text(self):
        return f'{len(self.item.automations)}'


class SequenceControlPane(TraitsDockPane):
    id = 'laba.sequencer.controls'
    name = 'Controls'

    movable = False
    closable = False
    floatable = False

    def traits_view(self):
        v = View(HGroup(icon_button_editor('start_button', 'start'),
                        icon_button_editor('stop_button', 'stop'),
                        spring,
                        # UItem('object.sequencer.timer', style='custom')
                        UItem('pause_button'),
                        UItem('continue_button'),
                        ))
        return v


class SequenceCentralPane(TraitsTaskPane):
    def traits_view(self):
        v = View(VGroup(UItem('object.sequencer.sequences',
                              editor=TabularEditor(selected='object.sequencer.selected_rows',
                                                   multi_select=True,
                                                   auto_update=True,
                                                   editable=False,
                                                   stretch_last_section=False,
                                                   adapter=SequenceAdapter())),

                        UItem('object.sequencer.selected.steps',
                              editor=TabularEditor(selected='object.sequencer.selected_step',
                                                   auto_update=True,
                                                   editable=False,
                                                   stretch_last_section=False,
                                                   adapter=SequenceStepAdapter())),
                        UItem('object.sequencer.selected_step', style='custom'),
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
