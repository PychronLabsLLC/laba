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
from threading import Thread

from loggable import Loggable
from traits.api import Button, Str, File
from traitsui.api import View, UItem, HGroup, spring

from paths import paths


class Automation(Loggable):
    text = Str
    path = File
    start_button = Button
    stop_button = Button

    _runthread = None

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
            self._runthread.run()

    # commands
    def _get_context(self):
        ctx = dict(info=self.info,
                   sleep=self.sleep)
        return ctx

    def sleep(self, nseconds):
        self.debug(f'sleep {nseconds}')
        st = time.time()
        while time.time() - st <= nseconds:
            time.sleep(0.5)

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

        try:

            st = time.time()
            func()
            # self.debug(
            #     "executed snippet estimated_duration={}, duration={}".format(
            #         self._estimated_duration, time.time() - st
            #     )
            # )
            print('asdfasasfasdfasd')
            self.debug('run complete')
        except Exception as e:
            exc = self.debug_exception()
            self.exception_trace = exc
            return exc

    def _start_button_fired(self):
        self.run()

    def traits_view(self):

        return View(HGroup(spring,
                           UItem('start_button'),
                           UItem('stop_button')))
# ============= EOF =============================================
