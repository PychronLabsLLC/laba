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
from traits.api import Instance
from communicator import Communicator
from loggable import Loggable
from util import import_klass


class Device(Loggable):
    communicator = Instance(Communicator)

    @classmethod
    def bootstrap(cls, cfg):
        obj = cls(name=cfg['name'])
        print(obj, obj.name, cfg['name'])
        obj.setup_communicator(cfg['communicator'])

        if obj.initialize():
            if obj.open():
                return obj

    def setup_communicator(self, cfg):
        kind = cfg['kind']
        klass = import_klass(f'communicator.{kind.capitalize()}Communicator')
        self.communicator = klass.bootstrap(cfg)

    def initialize(self):
        return True

    def open(self):
        return True
# ============= EOF =============================================
