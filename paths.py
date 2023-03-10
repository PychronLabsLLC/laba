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
import itertools
import os
from pathlib import Path


class Paths:
    def __init__(self):
        home = Path('~').expanduser()

        self.root = Path(home, 'plv')
        self.initialization_path = Path(self.root, 'init.yml')
        self.dashboards_path = Path(self.root, 'dashboard.yml')
        self.automations_path = Path(self.root, 'automations.yml')
        print(self.initialization_path)

    def get_automation_path(self, name):
        return Path(self.root, 'automations', name)

    def new_path(self, base, name, extension='.csv'):
        for i in itertools.count():
            p = Path(self.root, base, f'{name}{i:04n}{extension}')
            if not os.path.isfile(p):
                return p


paths = Paths()
# ============= EOF =============================================
