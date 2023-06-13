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

    def ask(self, *args, **kw):
        return self.communicator.ask(*args, **kw)

    def bootstrap(self, cfg):
        self.setup_communicator(cfg["communicator"])
        self.load(cfg)

    def load(self, cfg):
        pass

    def initialize(self):
        return True

    def open(self):
        return True

    def setup_communicator(self, cfg):
        kind = cfg["kind"]
        try:
            klass = import_klass(
                f"hardware.communicator.{kind.capitalize()}Communicator"
            )
        except AttributeError:
            try:
                klass = import_klass(
                    f"hardware.communicators.{kind.lower()}_communicator.{kind.capitalize()}Communicator"
                )
            except AttributeError:
                raise NotImplementedError(f"Failed loading communicator {kind}")

        self.communicator = klass(cfg)
        self.communicator.bootstrap()


# ============= EOF =============================================
