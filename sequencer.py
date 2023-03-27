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
from threading import Thread, Event

import yaml
from pyface.file_dialog import FileDialog
from traits.has_traits import on_trait_change
from traitsui.editors import TabularEditor, ListEditor, InstanceEditor
from traitsui.item import spring
from traitsui.tabular_adapter import TabularAdapter

from automation import Automation
from console import Console
from loggable import Loggable
from traits.api import List, File, Enum, Instance, Button, Dict, Any, Str, Bool, Int, Property, cached_property
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

    def __init__(self, cfg=None, ctx=None, *args, **kw):
        super().__init__(cfg, *args, **kw)
        if cfg is not None:
            self.automations = [Automation({'path': paths.get_automation_path(a)},
                                           ctx=ctx,
                                           application=self.application) for a in cfg['automations']]

    def run(self, console):
        ts = []
        for a in self.automations:
            try:
                # a.timer = timer
                a.timer = Timer()
                a.console = console
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


class LoadAutomationCTX():
    def __init__(self):
        self._memo = {}

    def __enter__(self):
        return self._memo

    # def __contains__(self, item):
    #     return item in self._memo
    #
    # def __setitem__(self, key, value):
    #     self._memo[key] = value

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class Sequence(Loggable):
    steps = List
    state = Enum('not run', 'running', 'failed', 'success')

    def __init__(self, cfg=None, *args, **kw):
        super().__init__(cfg, *args, **kw)
        if cfg is not None:
            with LoadAutomationCTX() as ctx:
                self.steps = [SequenceStep(si, application=self.application, ctx=ctx) for si in cfg['steps']]

    def cancel(self):
        for s in self.steps:
            for a in s.automations:
                a.cancel()

    def run(self, console):
        self.debug('run sequence')
        for i, si in enumerate(self.steps):
            self.debug(f'do step {i}')
            si.run(console)

    def toyaml(self):
        return {'name': self.name,
                'steps': [s.toyaml() for s in self.steps]}


def get_available_sequence_templates():
    return [os.path.splitext(p)[0] for p in os.listdir(paths.sequence_templates_dir)
            if p.endswith('.yaml') or p.endswith('.yml')]


def load_sequence_template(name):
    path = paths.get_sequence_template_path(name)
    return yload(path)


class Sequencer(Loggable):
    sequences = List(Sequence)
    path = File
    yobj = Dict
    selected = Instance(Sequence, ())
    selected_rows = List
    selected_step = Instance(SequenceStep, ())

    active_sequence = Instance(Sequence)

    sequence_template = Str
    available_sequence_templates = List

    console = Instance(Console, ())

    _runthread = None
    _cancel_evt = None

    edit_name = Str

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        self.available_sequence_templates = get_available_sequence_templates()
        if self.available_sequence_templates:
            self.sequence_template = self.available_sequence_templates[0]

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
        self.path = path
        with open(path, 'w') as wfile:
            yaml.dump({'sequences': ss}, wfile)

    def is_valid_automation(self, name):
        return os.path.isfile(paths.get_automation_path(name))

    def do_automation(self, a):
        self.debug('do automation {}'.format(a))
        self.sequences = [Sequence(application=self.application,
                                   cfg={'steps': [{'automations': [a]}]})]
        self.start()
        return True

    def start(self):
        self._cancel_evt = Event()
        self._runthread = Thread(target=self._run)
        self._runthread.start()

    # define a function to stop the runthread
    def stop(self):
        for s in self.sequences:
            s.cancel()

        self._cancel_evt.set()

    def add(self):
        # use the selected sequence template to create a new sequence
        if self.sequence_template:
            cfg = {'cfg': load_sequence_template(self.sequence_template)}

        else:
            idx = len(self.sequences)
            cfg = {'name': f'seq{idx:}'}

        seq = self.factory(Sequence, cfg)
        self.sequences.append(seq)

    def add_step(self):
        step = self.factory(SequenceStep, {'name': 'step'})
        self.selected.steps.append(step)

    def add_automation(self):
        automation = self.factory(Automation, {'path': paths.get_automation_path('foo')})
        self.selected_step.automations.append(automation)

    def factory(self, klass, kw):
        return klass(application=self.application, **kw)

    @on_trait_change('edit_+')
    def edit_handler(self, obj, name, old, new):
        if name == 'edit_name':
            name = 'name'
        for s in self.selected_rows:
            setattr(s, name, new)

    @on_trait_change('selected_rows[]')
    def handle_selected_rows(self, new):
        if new:
            self.selected = new[0]
            if self.selected.steps:
                self.selected_step = self.selected.steps[0]
            else:
                self.selected_step = self.factory(SequenceStep, {})
            self.edit_name = self.selected.name
        else:
            self.selected_step = None
            self.selected = None

    def _run(self):
        self.debug('run sequences')
        for s in self.sequences:
            self.active_sequence = s

            if self._cancel_evt.is_set():
                break

            delay = self._get_delay(s, 'delay_before')
            if delay:
                self._cancel_evt.wait(delay)
            try:
                s.state = 'running'
                s.run(self.console)
                s.state = 'success'
            except SequenceError as err:
                self.warning(f'Sequence {s} error: {err}')
                s.state = 'failed'

            delay = self._get_delay(s, 'delay_after')
            if delay:
                self._cancel_evt.wait(delay)

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
