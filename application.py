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
import os

from envisage.core_plugin import CorePlugin
from envisage.ui.tasks.tasks_application import TasksApplication
from envisage.ui.tasks.tasks_plugin import TasksPlugin
from pyface.tasks.task_window_layout import TaskWindowLayout

from db.db import DBClient
from hardware.device import Device
from loggable import Loggable
from paths import paths
from plugin import HardwarePlugin
from server import Server
from trigger import Trigger
from util import import_klass, yload


def make_device(cfg):
    klass = cfg.get("kind")
    if klass:
        klass = import_klass(f"hardware.{klass}")
    else:
        klass = Device

    dev = klass(cfg)
    dev.bootstrap(cfg)
    return dev


class Application(TasksApplication, Loggable):
    server = None

    dbclient = None

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.add_plugin(CorePlugin())
        self.add_plugin(TasksPlugin())
        self.add_plugin(HardwarePlugin())

        for plugin_obj in self._get_plugins():
            if plugin_obj.get("enabled", True):
                name = plugin_obj.get("name")
                if name == "SwitchPlugin":
                    klass = "plugins.switch_plugin.SwitchPlugin"
                elif name == "SpectrometerPlugin":
                    klass = "plugins.spectrometer_plugin.SpectrometerPlugin"
                elif name == "LaserPlugin":
                    klass = "plugins.laser_plugin.LaserPlugin"

                factory = import_klass(klass)
                plugin = factory()

                self.add_plugin(plugin)

    def start(self):
        self.initialize()
        return True

    def initialize(self):
        init = self._get_initization()
        self.dbclient = dbclient = DBClient()

        dbclient.build(drop=bool(int(os.environ.get("BUILD_DB", "0"))))

        dbclient.backup()

        for device_cfg in init.get("devices"):
            if device_cfg.get("enabled", True):
                device = make_device(device_cfg)
                if device:
                    self.register_service(Device, device)

                    dbclient.add_device(device.name)
                    dbclient.add_datastream("default", device.name)
                    device.on_trait_change(self._handle_device_update, "update")

                    for trigger in device_cfg.get("triggers", []):
                        trigger = Trigger(trigger)
                        device.on_trait_change(trigger.handle, "update")
                        device.triggers.append(trigger)

        server = init.get("server")

        if server:
            self.server = Server(application=self, port=server.get("port", 5555))
            self.server.run()

        # associate controller with each plugin
        for plugin_obj in self._get_plugins():
            if plugin_obj.get("enabled"):
                controller = plugin_obj.get("controller")
                if controller:
                    controller = self.get_service(Device, query=f'name=="{controller}"')
                    name = plugin_obj.get("name")
                    if name == "SwitchPlugin":
                        pid = "laba.plugin.switch"
                    elif name == "SpectrometerPlugin":
                        pid = "laba.plugin.spectrometer"
                    plugin = self.get_plugin(pid)
                    plugin.controller = controller

    def get_task(self, tid, activate=True):
        for win in self.windows:
            if win.active_task:
                if win.active_task.id == tid:
                    if activate and win.control:
                        win.activate()
                    break
        else:
            w = TaskWindowLayout(tid)
            win = self.create_window(w)
            print("asfasf", win)
            if activate:
                print("pppp")
                win.open()

        if win:
            if win.active_task:
                win.active_task.window = win

            return win.active_task

    def open_task(self, tid, **kw):
        return self.get_task(tid, True, **kw)

    # def _handle_trigger(self, trigger, obj, name, old, new):
    #     trigger.evaluate(obj, name, old, new)
    #     for test in trigger.get('tests', []):
    #         tvalue = test.get('value')
    #         comparator = test.get('comparator', '==')
    #         attribute = test.get('attribute', 'value')
    #         if attribute in new:
    #             v = new[attribute]
    #             result = eval(f'{tvalue} {comparator} {v}')
    #             if result:
    #                 self.info(f'Trigger fired, {trigger}')
    #                 action = trigger.get('action')
    #                 for k, v in action.items():
    #                     if k == 'log':
    #                         self.info(f'trigger log: {v}')
    #                 break

    def _handle_device_update(self, obj, name, old, new):
        self.debug(f"handling device update. {obj}, {new}")
        if new:
            dbclient = self.dbclient
            device_name = obj.name
            if "value" in new or "value_string" in new:
                dsname = new.get("datastream", "default")
                dbclient.add_measurement(dsname, device_name, **new)

            elif "datastream" in new:
                dbclient.add_datastream(new["datastream"], device_name, unique=False)

    # private
    def _get_initization(self):
        return yload(paths.initialization_path)

    def _get_plugins(self):
        yobj = yload(paths.initialization_path)
        return yobj.get("plugins", [])


# ============= EOF =============================================
