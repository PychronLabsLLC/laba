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
import yaml
from envisage.core_plugin import CorePlugin
from envisage.ui.tasks.tasks_application import TasksApplication
from envisage.ui.tasks.tasks_plugin import TasksPlugin

from hardware.device import Device
from loggable import Loggable
from paths import paths
from plugin import HardwarePlugin
from server import Server
from util import import_klass


class Application(TasksApplication, Loggable):
    server = None

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.add_plugin(CorePlugin())
        self.add_plugin(TasksPlugin())
        self.add_plugin(HardwarePlugin())

    def start(self):
        self.initialize()
        return True

    def initialize(self):
        init = self._get_initization()
        for device_cfg in init.get('devices'):
            if device_cfg.get('enabled', True):
                device = self._make_device(device_cfg)
                if device:
                    self.register_service(Device, device)

        server = init.get('server')
        if server:
            self.server = Server(application=self,
                                 port=server.get('port', 5555))
            self.server.run()

    # private
    def _make_device(self, cfg):
        klass = cfg.get('klass')
        if klass:
            klass = import_klass(f'hardware.{klass}')
        else:
            klass = Device
        dev = klass(cfg)
        dev.bootstrap(cfg)
        return dev

    def _get_initization(self):
        p = paths.initialization_path
        with open(p, 'r') as r:
            return yaml.load(r, yaml.SafeLoader)

# ============= EOF =============================================
