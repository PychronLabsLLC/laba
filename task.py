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
from envisage.ui.tasks.action.exit_action import ExitAction
from envisage.ui.tasks.action.preferences_action import PreferencesGroup
from envisage.ui.tasks.action.task_window_launch_group import TaskWindowLaunchAction, TaskWindowLaunchGroup
from pyface.action.schema.schema import SMenuBar, SMenu
from pyface.constant import OK
from pyface.file_dialog import FileDialog
from pyface.tasks.action.dock_pane_toggle_group import DockPaneToggleGroup
from pyface.tasks.task import Task
from pyface.tasks.task_layout import TaskLayout, PaneItem
from traits.api import Instance, List, Any, Button, DelegatesTo
from traitsui.menu import Action

from automation import Automation
from dashboard import Dashboard, BaseDashboard
from hardware.device import Device
from loggable import Loggable
from pane import HardwareCentralPane, DevicesPane, DashboardsPane, AutomationsPane, SequenceEditorPane, \
    SequenceCentralPane, SequenceControlPane
from paths import paths
from plugin_manager import PluginManager
from sequencer import Sequencer


class PluginManagerAction(Action):
    name = 'Manage...'

    def perform(self, event):
        plugin_manager = PluginManager()
        plugin_manager.edit_traits()


class OpenSequenceAction(Action):
    name = 'Open Sequence...'

    def perform(self, event):
        dlg = FileDialog(action='open', default_directory=str(paths.sequences_dir))
        if dlg.open() == OK:
            task = event.task.window.application.get_task('laba.sequencer.task', False)
            if task.open(dlg.path):
                task.window.open()


class BaseTask(Task):
    menu_bar = SMenuBar(
        SMenu(
            OpenSequenceAction(),
            ExitAction(),
            PreferencesGroup(),
            id='file.menu',
            name='&File'
        ),
        SMenu(TaskWindowLaunchGroup(),
              DockPaneToggleGroup(),
              id="view.menu",
              name="&View"),
        SMenu(
            # OpenAction(),
            # SaveAction(),
            PluginManagerAction(),
            id='plugin.menu',
            name='Plugins',
        )
    )


class SequencerTask(BaseTask):
    id = 'laba.sequence.task'
    name = 'Sequencer'

    sequencer = Instance(Sequencer, ())
    # timer = DelegatesTo('sequencer')
    # timer = DelegatesTo('sequencer')

    start_button = Button
    add_button = Button
    save_button = Button
    save_as_button = Button

    def _sequencer_default(self):
        s = Sequencer(application=self.application)
        return s

    def _start_button_fired(self):
        self.sequencer.start()

    def _add_button_fired(self):
        self.sequencer.add()

    def _save_button_fired(self):
        self.sequencer.save()

    def _save_as_button_fired(self):
        self.sequencer.save_as()

    def _pause_button_fired(self):
        pass

    def _continue_button_fired(self):
        pass

    def create_dock_panes(self):
        return [SequenceEditorPane(model=self),
                SequenceControlPane(model=self)]

    def create_central_pane(self):
        return SequenceCentralPane(model=self)

    def open(self, path):
        self.sequencer.path = path
        self.sequencer.load()

    def _default_layout_default(self):
        return TaskLayout(top=PaneItem("laba.sequencer.controls"),
                          left=PaneItem("laba.sequencer.editor"))


class HardwareTask(BaseTask):
    name = 'Hardware'
    id = 'laba.hardware.task'
    selection = Instance(Loggable)
    devices = List(Device)
    dashboards = List(BaseDashboard)
    automations = List(Automation)

    def create_dock_panes(self):
        return [DevicesPane(model=self),
                DashboardsPane(model=self),
                AutomationsPane(model=self)]

    def create_central_pane(self):
        return HardwareCentralPane(model=self)

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem("laba.devices"))
# ============= EOF =============================================
