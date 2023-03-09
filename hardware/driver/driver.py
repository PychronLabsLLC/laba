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
from hardware.communicator import Communicator
from loggable import Loggable
from util import import_klass
from traits.api import Instance


class Driver(Loggable):
    communicator = Instance(Communicator)

    def bootstrap(self, cfg):
        self.setup_communicator(cfg['communicator'])

    def setup_communicator(self, cfg):
        kind = cfg['kind']
        klass = import_klass(f'hardware.communicator.{kind.capitalize()}Communicator')
        self.communicator = klass(cfg)
# ============= EOF =============================================
