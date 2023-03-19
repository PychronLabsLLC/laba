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
import os

import yaml
from traitsui.editors import TabularEditor, ListEditor, InstanceEditor
from traitsui.item import spring
from traitsui.tabular_adapter import TabularAdapter

from automation import Automation
from loggable import Loggable
from traits.api import List, File, Enum, Instance, Button
from traitsui.api import View, UItem, HGroup, VGroup

from paths import paths
from util import yload, icon_button_editor


class SequenceError(BaseException):
    pass


class AutomationError(BaseException):
    pass


class SequenceStep(Loggable):
    automations = List

    def __init__(self, cfg=None, *args, **kw):
        super().__init__(cfg, *args, **kw)
        if cfg is not None:
            self.automations = [Automation({'path': paths.get_automation_path(a)}) for a in cfg['automations']]

    def run(self):
        ts = []
        for a in self.automations:
            try:
                t = a.run(block=False)
                ts.append(t)
            except AutomationError as err:
                self.warning(f'Automation {a} error: {err}')
                break

        for ti in ts:
            ti.join()

    def toyaml(self):
        return {'name': self.name,
                'automations': [os.path.basename(a.path) for a in self.automations]}

    def traits_view(self):
        v = View(UItem('automations', editor=ListEditor(style='custom',
                                                        editor=InstanceEditor())))
        return v


class Sequence(Loggable):
    steps = List
    state = Enum('not run', 'running', 'failed', 'success')

    def __init__(self, cfg=None, *args, **kw):
        if cfg is not None:
            self.steps = [SequenceStep(si) for si in cfg['steps']]

        super().__init__(cfg, *args, **kw)

    def run(self):
        self.debug('run sequence')
        for i, si in enumerate(self.steps):
            self.debug(f'do step {i}')
            si.run()

    def toyaml(self):
        return {'name': self.name,
                'steps': [s.toyaml() for s in self.steps]}


class Sequencer(Loggable):
    sequences = List(Sequence)
    path = File

    def load(self):
        self.sequences = yload(self.path)

    def save(self):
        pass

    def run(self):
        self.debug('run sequences')
        for s in self.sequences:
            try:
                s.run()
            except SequenceError as err:
                self.warning(f'Sequence {s} error: {err}')


class SequenceAdapter(TabularAdapter):
    columns = [('Name', 'name')]

    def _get_bg_color(self):
        if self.item.state == 'not run':
            color = 'gray'
        elif self.item.state == 'running':
            color = 'yellow'
        elif self.item.state == 'success':
            color = 'green'
        elif self.item.state == 'failed':
            color = 'gray'
        return color


class SequenceStepAdapter(TabularAdapter):
    columns = [('Name', 'name')]


class SequenceEditor(Loggable):
    sequences = List(Sequence)
    path = File
    selected = Instance(Sequence, ())
    selected_step = Instance(SequenceStep, ())
    add = Button
    add_step = Button

    save = Button

    def load(self):
        self.sequences = [Sequence(si) for si in yload(self.path)]

    def _add_fired(self):
        self.debug('add fired')
        s = Sequence()
        self.sequences.append(s)

    def _add_step_fired(self):
        s = SequenceStep()
        self.selected.steps.append(s)

    def _save_fired(self):
        ss = []
        for si in self.sequences:
            ss.append(si.toyaml())

        with open('./demo_save.yaml', 'w') as wfile:
            yaml.dump(ss, wfile)

    def traits_view(self):
        cgrp = HGroup(icon_button_editor('add', 'add'), spring,
                      icon_button_editor('add_step', 'brick-add'),
                      icon_button_editor('save', 'save'))

        v = View(cgrp,
                 HGroup(UItem('sequences',
                              editor=TabularEditor(selected='selected',
                                                   adapter=SequenceAdapter())),
                        UItem('object.selected.steps',
                              editor=TabularEditor(selected='selected_step',
                                                   adapter=SequenceStepAdapter()))),
                 UItem('selected_step', style='custom'),
                 width=500,
                 resizable=True)
        return v


if __name__ == '__main__':
    s = SequenceEditor()
    s.path = './demo.yaml'
    s.load()
    s.configure_traits()

# ============= EOF =============================================
