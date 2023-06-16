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
from pyface.tasks.task_layout import TaskLayout, PaneItem
from traits.trait_types import Instance, Button

from pane import (
    SequenceEditorPane,
    SequenceControlPane,
    ConsolePane,
    SequenceCentralPane,
)
from sequencer import Sequencer
from task import BaseTask


class SequencerTask(BaseTask):
    id = "laba.sequence.task"
    name = "Sequencer"

    sequencer = Instance(Sequencer)

    start_button = Button
    stop_button = Button
    pause_button = Button
    continue_button = Button

    add_button = Button
    add_step_button = Button
    add_automation_button = Button

    save_button = Button
    save_as_button = Button

    def _sequencer_default(self):
        s = Sequencer(application=self.application)
        return s

    def _pause_button_fired(self):
        # for a in self.sequencer.selected_step.automations:
        #     a.timer.pause()
        seq = self.sequencer.active_sequence
        if seq:
            for step in seq.steps:
                for a in step.automations:
                    a.timer.pause()

    def _start_button_fired(self):
        self.sequencer.start()

    def _stop_button_fired(self):
        self.sequencer.stop()

    def _add_button_fired(self):
        self.sequencer.add()

    def _add_step_button_fired(self):
        self.sequencer.add_step()

    def _add_automation_button_fired(self):
        self.sequencer.add_automation()

    def _save_button_fired(self):
        self.sequencer.save()

    def _save_as_button_fired(self):
        self.sequencer.save_as()

    def create_dock_panes(self):
        return [
            SequenceEditorPane(model=self),
            SequenceControlPane(model=self),
            ConsolePane(model=self.sequencer),
        ]

    def create_central_pane(self):
        return SequenceCentralPane(model=self)

    def open(self, path):
        self.sequencer.path = path
        self.sequencer.load()

    def do_automation(self, name):
        return self.sequencer.do_automation(name)

    def is_valid_automation(self, name):
        return self.sequencer.is_valid_automation(name)

    def _default_layout_default(self):
        return TaskLayout(
            top=PaneItem("laba.sequencer.controls"),
            left=PaneItem("laba.sequencer.editor"),
            right=PaneItem("laba.console"),
        )


# ============= EOF =============================================
