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
import time
from datetime import datetime
from threading import Thread, Event

from console import Console
from hardware import SwitchController
from hardware.device import Device
from loggable import Loggable
from traits.api import Button, Str, File, Any, Bool, Instance
from traitsui.api import View, UItem, HGroup, spring

from paths import paths
from persister import CSVPersister
from timer import Timer

REGISTRY = []


def register(func):
    REGISTRY.append(func.__name__)
    return func


def is_alive(func):
    def wrapper(obj, *args, **kw):
        print(obj, args, kw)
        if obj.alive:
            return func(obj, *args, **kw)

    register(func)
    return wrapper


def contributed_is_alive(func, obj):
    def wrapper(*args, **kw):
        if obj.alive:
            return func(*args, **kw)

    register(func)
    return wrapper


class Automation(Loggable):
    application = Any
    text = Str
    path = File

    alive = Bool
    timer = Instance(Timer, ())
    console = Instance(Console)

    _runthread = None
    _recording_thread = None
    _recording_event = None

    def __init__(self, cfg=None, ctx=None, *args, **kw):
        super().__init__(cfg=cfg, *args, **kw)
        if cfg:
            self.load(cfg["path"], ctx=ctx)

    def load(self, path=None, ctx=None):
        if path is None:
            path = self.path
        else:
            if isinstance(path, str):
                path = paths.get_automation_path(path)

        if not path:
            self.warning(f"No path for {self}")
            return

        self.path = path
        if ctx is not None:
            if str(path) in ctx:
                self.debug("using context")
                self.text = ctx[str(path)]
                return
        self.debug(f"loading {path}")
        with open(self.path, "r") as rfile:
            self.text = rfile.read()

        if ctx is not None:
            ctx[str(path)] = self.text

    def run(self, block=False):
        self.load()

        if block:
            self._run()
        else:
            self._runthread = Thread(target=self._run, daemon=True)
            self._runthread.start()
            return self._runthread

    def cancel(self):
        self.alive = False
        self.timer.cancel()

    # commands
    @is_alive
    def dev_function(self, device, name, *args, **kw):
        """
        call a function on a device

        :param device:
        :param name:
        :param args:
        :param kw:
        :return:
        """
        dev = self.application.get_service(Device, query=f"name=='{device}'")
        if dev is None:
            self.warning(f"Invalid device {device}")
            return

        if not hasattr(dev, name):
            self.warning(f"Invalid function {name}")
            return

        func = getattr(dev, name)
        func(*args, **kw)

    @is_alive
    def sleep(self, nseconds):
        self.debug(f"sleep {nseconds}")
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
    def start_recording(self, attributes, period=1):
        self._recording_event = Event()

        def func():
            st = time.time()
            with CSVPersister(path_name="datalog") as writer:
                attribute_names = [":".join(a) for a in attributes]
                # write header
                writer.write(
                    [
                        "timestamp",
                        "elapsed_time",
                    ]
                    + attribute_names
                )

                while not self._recording_event.is_set():
                    sti = time.time()

                    # get all the values that need to be recorded
                    now = datetime.now()
                    row = [now.isoformat(), time.time() - st]

                    for a in attributes:
                        if len(a) == 2:
                            device, function = a
                            args, kwargs = [], {}
                        elif len(a) == 3:
                            device, function, args = a
                            kwargs = {}
                        elif len(a) == 4:
                            device, function, args, kwargs = a

                        row.append(self.dev_function(device, function, *args, **kwargs))
                    writer.write(row)

                    pe = max(0, period - (time.time() - sti))
                    if pe:
                        time.sleep(pe)

        self._recording_thread = Thread(target=func, daemon=True)
        self._recording_thread.start()

    @register
    def stop_recording(self):
        if self._recording_event:
            self._recording_event.set()

    def finish(self):
        self.stop_recording()

    def debug(self, msg):
        if self.console:
            dt = datetime.now().strftime("%H:%M:%S")
            self.console.text += f"{dt} -- {msg}\n"
        super().debug(msg)

    # private
    def _run(self):
        self.debug("starting run")
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
            self.debug("run complete")

        except Exception as e:
            exc = self.debug_exception()
            self.exception_trace = exc
            return exc
        finally:
            self.finish()

    # command helpers
    def _get_context(self):
        ctx = {}
        for name in REGISTRY:
            ctx[name] = getattr(self, name)

        ctx["info"] = self.info
        messages = self.application.get_extensions("laba.automation.commands")

        ctx.update({n: contributed_is_alive(f, self) for n, f in messages})

        return ctx

    def traits_view(self):
        return View(HGroup(UItem("path"), spring, UItem("timer", style="custom")))

    # def _start_button_fired(self):
    #     self.run()
    #
    # def traits_view(self):
    #
    #     return View(HGroup(spring,
    #                        UItem('start_button'),
    #                        UItem('stop_button')))


# ============= EOF =============================================
