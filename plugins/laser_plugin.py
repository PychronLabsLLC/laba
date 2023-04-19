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
from envisage.ui.tasks.task_factory import TaskFactory

from plugin import BasePlugin
from tasks.laser_task import LaserTask


class LaserPlugin(BasePlugin):
    def _laser_task_factory(self):
        return LaserTask(application=self.application)

    def _tasks_default(self):
        return [
            TaskFactory(
                id="laba.laser.task",
                name="Laser",
                factory=self._laser_task_factory,
            )
        ]


class ChromiumPlugin(LaserPlugin):
    pass


# ============= EOF =============================================
