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

from loggable import Loggable


def add_extension(name, ext=".yaml"):
    if not isinstance(name, str):
        if not name.suffix == ext:
            name = name.with_suffix(name, ext)
    else:
        if not name.endswith(ext):
            name = f"{name}{ext}"
    return name


class Paths(Loggable):
    def __init__(self, *args, **kw):
        # self.root = Path(home, 'laba')
        # get root from environment if it exists otherwise use default '~/laba'
        super().__init__(*args, **kw)
        home = Path("~").expanduser()
        default = Path(home, "laba")

        self.root = Path(os.environ.get("LABA_ROOT", default))

        self.initialization_path = Path(self.root, "init.yml")
        self.dashboards_path = Path(self.root, "dashboard.yml")
        self.automations_path = Path(self.root, "automations.yml")
        self.database_path = Path(self.root, "recorder.db")
        self.database_backup_path = Path(self.root, "backups", "backup.db")
        self.sequences_dir = Path(self.root, "sequences")
        self.sequence_templates_dir = Path(self.root, "sequence_templates")

        # make defaults
        self.make_dir("backups")
        self.make_dir("sequences")
        self.make_dir("automations")
        self.make_dir("sequence_templates")

    def make_dir(self, *basename):
        rp = Path(self.root, *basename)
        if not rp.is_dir():
            rp.mkdir()

    def get_automation_path(self, name):
        return self.get_py_path("automations", name)

    def get_sequence_template_path(self, name):
        return self.get_yaml_path("sequence_templates", name)

    def get_py_path(self, base, name):
        return self.get_extension_path(base, name, (".py",))

    def get_yaml_path(self, base, name):
        return self.get_extension_path(base, name, (".yml", ".yaml"))

    def get_extension_path(self, base, name, extensions):
        for e in extensions:
            namee = add_extension(name, e)
            p = Path(self.root, base, namee)
            print(p)
            if os.path.isfile(p):
                return p
        else:
            self.debug(
                f"failed to construct a path that exists, {base}, {name}, {extensions}"
            )

    def new_path(self, base, name, extension=".csv"):
        rp = Path(self.root, base)
        if not rp.is_dir():
            rp.mkdir()

        for i in itertools.count():
            p = Path(self.root, base, f"{name}{i:04n}{extension}")
            if not os.path.isfile(p):
                return p

    def database_backups(self):
        now = int(datetime.now().timestamp())
        return Path(self.root, "backups", f"{now}.backup.db")


paths = Paths()
# ============= EOF =============================================
