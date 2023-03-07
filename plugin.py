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
from envisage.plugin import Plugin
from envisage.ui.tasks.task_factory import TaskFactory

from device import Device
from loggable import Loggable
from traits.api import List

from task import HardwareTask


class BasePlugin(Plugin, Loggable):
    service_offers = List(contributes_to="envisage.service_offers")
    preferences = List(contributes_to="envisage.preferences")
    preferences_panes = List(contributes_to="envisage.ui.tasks.preferences_panes")
    tasks = List(contributes_to="envisage.ui.tasks.tasks")


class HardwarePlugin(BasePlugin):
    def _task_factory(self):
        devices = self.application.get_services(Device)
        return HardwareTask(devices=devices)

    def _tasks_default(self):
        return [TaskFactory(
                id="plv.hardware.task",
                name="Hardware",
                factory=self._task_factory,
                # image="repo",
            )]
# ============= EOF =============================================
