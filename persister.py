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
import json

import yaml
from traits.api import File, Str

import csv

from loggable import Loggable
from paths import paths


class Persister(Loggable):
    path = File
    path_name = Str

    def write(self, data):
        if isinstance(data, dict):
            pass
        self._write_hook(data)

    def __enter__(self):
        self.path = self._new_path(self.path_name)
        self._handle = open(self.path, 'w')
        self._enter_hook()

        return self

    def flush(self):
        self._handle.flush()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._handle.close()

    def _new_path(self, *args, **kw):
        return paths.new_path('persistence', *args, **kw)

    def _enter_hook(self):
        pass

    def _write_hook(self, data):
        pass


class CSVPersister(Persister):
    def _enter_hook(self):
        self._writer = csv.writer(self._handle)

    def _write_hook(self, data):
        self._writer.writerow(data)


class JSONPersister(Persister):
    def _enter_hook(self):
        pass

    def _write_hook(self, data):
        json.dump(data, self._handle)


class YAMLPersister(Persister):
    def _enter_hook(self):
        pass

    def _write_hook(self, data):
        yaml.dump(data, self._handle)


# define a class for writing txt to a file
class TextPersister(Persister):
    def _enter_hook(self):
        pass

    def _write_hook(self, data):
        self._handle.write(data)

# ============= EOF =============================================
