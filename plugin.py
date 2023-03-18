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
import yaml
from envisage.plugin import Plugin
from envisage.ui.tasks.task_factory import TaskFactory

from automation import Automation
from dashboard import Dashboard, HistoryDashboard
from hardware.device import Device
from loggable import Loggable
from traits.api import List

from paths import paths
from task import HardwareTask


class BasePlugin(Plugin, Loggable):
    service_offers = List(contributes_to="envisage.service_offers")
    preferences = List(contributes_to="envisage.preferences")
    preferences_panes = List(contributes_to="envisage.ui.tasks.preferences_panes")
    tasks = List(contributes_to="envisage.ui.tasks.tasks")


class HardwarePlugin(BasePlugin):
    def _task_factory(self):
        devices = self.application.get_services(Device)

        ds = [HistoryDashboard(self.application)]

        with open(paths.dashboards_path, 'r') as rfile:
            yobj = yaml.load(rfile, yaml.SafeLoader)
            for d in yobj:
                ds.append(Dashboard(self.application, d))

        automations = []
        with open(paths.automations_path, 'r') as rfile:
            yobj = yaml.load(rfile, yaml.SafeLoader)
            for automation in yobj:
                automations.append(Automation(automation))

        return HardwareTask(devices=devices, dashboards=ds, automations=automations,
                            selection=ds[0])

    def _tasks_default(self):
        return [TaskFactory(
                id="plv.hardware.task",
                name="Hardware",
                factory=self._task_factory,
                # image="repo",
            )]
# ============= EOF =============================================
