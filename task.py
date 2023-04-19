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
from envisage.ui.tasks.action.task_window_launch_group import TaskWindowLaunchGroup
from pyface.action.schema.schema import SMenuBar, SMenu
from pyface.constant import OK
from pyface.file_dialog import FileDialog
from pyface.tasks.action.dock_pane_toggle_group import DockPaneToggleGroup
from pyface.tasks.task import Task
from pyface.tasks.task_layout import TaskLayout, PaneItem
from traits.api import Instance, List
from traitsui.menu import Action

from automation import Automation
from dashboard import BaseDashboard
from hardware.device import Device
from loggable import Loggable
from pane import HardwareCentralPane, DevicesPane, DashboardsPane, AutomationsPane
from paths import paths
from plugin_manager import PluginManager


class PluginManagerAction(Action):
    name = "Manage..."

    def perform(self, event):
        plugin_manager = PluginManager()
        plugin_manager.edit_traits()


class OpenSequenceAction(Action):
    name = "Open Sequence..."

    def perform(self, event):
        dlg = FileDialog(action="open", default_directory=str(paths.sequences_dir))
        if dlg.open() == OK:
            task = event.task.window.application.get_task("laba.sequencer.task", False)
            if task.open(dlg.path):
                task.window.open()


class BaseTask(Task):
    menu_bar = SMenuBar(
        SMenu(
            OpenSequenceAction(),
            ExitAction(),
            PreferencesGroup(),
            id="file.menu",
            name="&File",
        ),
        SMenu(
            TaskWindowLaunchGroup(), DockPaneToggleGroup(), id="view.menu", name="&View"
        ),
        SMenu(
            # OpenAction(),
            # SaveAction(),
            PluginManagerAction(),
            id="plugin.menu",
            name="Plugins",
        ),
    )


class HardwareTask(BaseTask):
    name = "Hardware"
    id = "laba.hardware.task"
    selection = Instance(Loggable)
    devices = List(Device)
    dashboards = List(BaseDashboard)
    automations = List(Automation)

    def create_dock_panes(self):
        return [
            DevicesPane(model=self),
            DashboardsPane(model=self),
            AutomationsPane(model=self),
        ]

    def create_central_pane(self):
        return HardwareCentralPane(model=self)

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem("laba.devices"))


# ============= EOF =============================================
