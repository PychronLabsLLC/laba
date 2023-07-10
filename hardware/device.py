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
import math
import random

from numpy import polyval
from traits.api import Instance, Event, HasTraits, Str, List

from hardware.driver.driver import Driver
from loggable import Loggable
from util import import_klass
from traitsui.api import View, Item


class Device(Loggable):
    driver = Instance(Driver)
    update = Event
    triggers = List

    def traits_view(self):
        return View(Item("name"))

    def bootstrap(self, cfg):
        self.load(cfg)
        self.setup_driver(cfg["driver"])
        if self.open():
            if self.initialize():
                return True

    def load(self, cfg):
        pass

    def setup_driver(self, cfg):
        kind = cfg["kind"]
        klass = import_klass(f"integrations.drivers.{kind}")
        self.driver = klass(cfg)
        self.driver.bootstrap(cfg)

    def initialize(self):
        r = self.driver.initialize()
        if r:
            self.initialize_hook()

        return r

    def initialize_hook(self):
        pass

    def open(self):
        return self.driver.open()

    def get_value(self, *args, **kw):
        return random.random() + math.log(id(self))


# ============= EOF =============================================
