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
import time
from datetime import datetime
from threading import Thread, Event

from hardware import SwitchController
from hardware.device import Device
from loggable import Loggable
from traits.api import Button, Str, File, Any, Bool, Instance
from traitsui.api import View, UItem, HGroup, spring

from paths import paths
from persister import CSVPersister
from timer import Timer


def is_alive(func):
    def wrapper(obj, *args, **kw):
        if obj.alive:
            return func(obj, *args, **kw)

    return wrapper


class Automation(Loggable):
    application = Any
    text = Str
    path = File
    # start_button = Button
    # stop_button = Button
    alive = Bool
    timer = Instance(Timer)

    _runthread = None
    _recording_thread = None
    _recording_event = None

    def __init__(self, cfg=None, *args, **kw):
        super().__init__(cfg=cfg, *args, **kw)
        if cfg:
            self.load(cfg['path'])

    def load(self, path=None):
        if path is None:
            path = self.path
        else:
            path = paths.get_automation_path(path)

        self.path = path
        self.debug(f'loading {path}')
        with open(self.path, 'r') as rfile:
            self.text = rfile.read()

    def run(self, block=False):

        self.load()

        if block:
            self._run()
        else:
            self._runthread = Thread(target=self._run)
            self._runthread.start()
            return self._runthread

    # commands
    def _get_context(self):
        ctx = dict(info=self.info,
                   sleep=self.sleep,
                   open_switch=self.open_switch,
                   close_switch=self.close_switch,
                   start_recording=self.start_recording)
        return ctx

    def open_switch(self, name, *args, **kw):
        self._actuate_switch(name, True, *args, **kw)

    def close_switch(self, name, *args, **kw):
        self._actuate_switch(name, False, *args, **kw)

    @is_alive
    def _actuate_switch(self, name, state, *args, **kw):
        for sw in self.application.get_services(Device):
            if not hasattr(sw, 'switches'):
                continue

            for si in sw.switches:
                if si.name == name:
                    func = sw.open_switch if state else sw.close_switch
                    func(name, *args, **kw)
                    break

    @is_alive
    def sleep(self, nseconds):
        self.debug(f'sleep {nseconds}')
        if nseconds > 3 and self.timer:
            self.timer.max_value = nseconds
            self.timer.start()
        else:

            st = time.time()
            while time.time() - st <= nseconds:
                if not self.alive:
                    break
                time.sleep(0.5)

    @is_alive
    def start_recording(self):
        self._recording_event = Event()

        def func():
            st = time.time()
            period = 1
            with CSVPersister(path_name='datalog') as writer:
                while not self._recording_event.is_set():
                    sti = time.time()

                    # get all the values that need to be recorded
                    now = datetime.now()
                    writer.write([now.isoformat(), time.time() - st])

                    pe = max(0, period - (time.time() - sti))
                    if pe:
                        time.sleep(pe)

        self._recording_thread = Thread(target=func)
        self._recording_thread.start()

    def stop_recording(self):
        if self._recording_event:
            self._recording_event.set()

    def finish(self):
        self.stop_recording()

    def _run(self):
        self.debug('starting run')
        try:
            code = compile(self.text, "<string>", "exec")
        except BaseException as e:
            exc = self.debug_exception()
            self.exception_trace = exc
            return e

        ctx = self._get_context()
        try:
            exec(code, ctx)
            func = ctx["main"]
        except KeyError as e:
            exc = self.debug_exception()
            self.exception_trace = exc
            return

        self.alive = True
        try:
            func()
            self.debug('run complete')

        except Exception as e:
            exc = self.debug_exception()
            self.exception_trace = exc
            return exc
        finally:
            self.finish()

    def traits_view(self):
        return View(UItem('path'))
    # def _start_button_fired(self):
    #     self.run()
    #
    # def traits_view(self):
    #
    #     return View(HGroup(spring,
    #                        UItem('start_button'),
    #                        UItem('stop_button')))
# ============= EOF =============================================
