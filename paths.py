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
from datetime import datetime
from pathlib import Path


def add_extension(name, ext='.yaml'):
    if not isinstance(name, str):
        if not name.suffix == ext:
            name = name.with_suffix(name, ext)
    else:
        if not name.endswith(ext):
            name = f'{name}{ext}'
    return name


class Paths:
    def __init__(self):
        home = Path('~').expanduser()

        self.root = Path(home, 'laba')
        self.initialization_path = Path(self.root, 'init.yml')
        self.dashboards_path = Path(self.root, 'dashboard.yml')
        self.automations_path = Path(self.root, 'automations.yml')
        self.database_path = Path(self.root, 'recorder.db')
        self.database_backup_path = Path(self.root, 'backups', 'backup.db')
        self.sequences_dir = Path(self.root, 'sequences')

        # make defaults
        self.make_dir('backups')
        self.make_dir('sequences')

    def make_dir(self, *basename):
        rp = Path(self.root, *basename)
        if not rp.is_dir():
            rp.mkdir()

    def get_automation_path(self, name):
        name = add_extension(name, '.py')
        return Path(self.root, 'automations', name)

    def new_path(self, base, name, extension='.csv'):
        rp = Path(self.root, base)
        if not rp.is_dir():
            rp.mkdir()

        for i in itertools.count():
            p = Path(self.root, base, f'{name}{i:04n}{extension}')
            if not os.path.isfile(p):
                return p

    def database_backups(self):
        now = int(datetime.now().timestamp())
        return Path(self.root, 'backups', f'{now}.backup.db')


paths = Paths()
# ============= EOF =============================================
