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
import time
from threading import Thread

import yaml
from pyface.file_dialog import FileDialog
from traitsui.editors import TabularEditor, ListEditor, InstanceEditor
from traitsui.item import spring
from traitsui.tabular_adapter import TabularAdapter

from automation import Automation
from loggable import Loggable
from traits.api import List, File, Enum, Instance, Button, Dict, Any
from traitsui.api import View, UItem, HGroup, VGroup

from paths import paths, add_extension
from timer import Timer
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
            self.automations = [Automation({'path': paths.get_automation_path(a)},
                                           application=self.application) for a in cfg['automations']]

    def run(self, timer):
        ts = []
        for a in self.automations:
            try:
                a.timer = timer
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
        super().__init__(cfg, *args, **kw)

        if cfg is not None:
            self.steps = [SequenceStep(si, application=self.application) for si in cfg['steps']]

    def run(self, timer):
        self.debug('run sequence')
        for i, si in enumerate(self.steps):
            self.debug(f'do step {i}')
            si.run(timer)

    def toyaml(self):
        return {'name': self.name,
                'steps': [s.toyaml() for s in self.steps]}


class Sequencer(Loggable):
    sequences = List(Sequence)
    path = File
    yobj = Dict
    selected = Instance(Sequence, ())
    timer = Instance(Timer, ())
    _runthread = None

    def load(self):
        yobj = yload(self.path)
        self.yobj = yobj
        self.sequences = [Sequence(s, application=self.application) for s in yobj['sequences']]

    def save(self):
        if self.path:
            self._save(self.path)
        else:
            self.save_as()

    def save_as(self):
        dlg = FileDialog(action='save as',
                         wildcard='.yaml',
                         default_directory=str(paths.sequences_dir))
        if dlg.open():
            self._save(dlg.path)

    def _save(self, path):
        ss = []
        for si in self.sequences:
            ss.append(si.toyaml())

        path = add_extension(path, '.yaml')
        with open(path, 'w') as wfile:
            yaml.dump({'sequences': ss}, wfile)

    def start(self):
        self._runthread = Thread(target=self._run)
        self._runthread.start()

    def add(self):
        self.sequences.append(Sequence())

    def _run(self):
        self.debug('run sequences')
        for s in self.sequences:
            delay = self._get_delay(s, 'delay_before')
            if delay:
                time.sleep(delay)
            try:
                s.state = 'running'
                s.run(self.timer)
                s.state = 'success'
            except SequenceError as err:
                self.warning(f'Sequence {s} error: {err}')
                s.state = 'failed'

            delay = self._get_delay(s, 'delay_after')
            if delay:
                time.sleep(delay)

    def _get_delay(self, s, key):
        delay = s.get(key)
        if delay is None:
            delay = self.yobj.get(key, 0)

        return delay


class SequenceStepAdapter(TabularAdapter):
    columns = [('Name', 'name')]


# class SequenceEditor(Loggable):
#     sequences = List(Sequence)
#     path = File
#     selected = Instance(Sequence, ())
#     selected_step = Instance(SequenceStep, ())
#     add = Button
#     add_step = Button
#     add_automation = Button
#
#     save = Button
#
#     def load(self):
#         yobj = yload(self.path)
#         self.sequences = [Sequence(si) for si in yobj['sequences']]
#
#     def _add_fired(self):
#         self.debug('add fired')
#         s = Sequence()
#         self.sequences.append(s)
#
#     def _add_step_fired(self):
#         s = SequenceStep()
#         self.selected.steps.append(s)
#
#     def _add_automation_fired(self):
#         a = Automation()
#         self.selected_step.automations.append(a)
#
#     def _save_fired(self):
#         ss = []
#         for si in self.sequences:
#             ss.append(si.toyaml())
#
#         with open('./demo_save.yaml', 'w') as wfile:
#             yaml.dump({'sequences': ss}, wfile)

# def traits_view(self):
#     cgrp = HGroup(icon_button_editor('add', 'add'), spring,
#                   icon_button_editor('add_step', 'brick-add'),
#                   icon_button_editor('save', 'save'))
#
#     v = View(cgrp,
#              HGroup(UItem('sequences',
#                           editor=TabularEditor(selected='selected',
#                                                adapter=SequenceAdapter())),
#                     UItem('object.selected.steps',
#                           editor=TabularEditor(selected='selected_step',
#                                                adapter=SequenceStepAdapter()))),
#              UItem('selected_step', style='custom'),
#              width=500,
#              resizable=True)
#     return v


# if __name__ == '__main__':
#     s = SequenceEditor()
#     s.path = './demo.yaml'
#     s.load()
#     s.configure_traits()

# ============= EOF =============================================
