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
from threading import Thread, Event
from pyface.gui import GUI
from traitsui.qt4.extra.led_editor import LEDEditor

from loggable import Loggable
from traits.api import Float, Button, Bool, Str
from traitsui.api import View, UItem, HGroup, VGroup, spring, ButtonEditor


class Timer(Loggable):
    current_value = Float
    display_value = Float
    max_value = Float

    _thread = None
    _evt = None
    _paused = None

    pause_button = Button('Pause')
    continue_button = Button('Continue')
    start_button = Button('Start')
    start_enabled = Bool(True)
    pause_enabled = Bool(False)
    continue_enabled = Bool(False)
    pause_label = Str('Pause')

    def _start_button_fired(self):
        self.start(block=False)

    def _pause_button_fired(self):
        if self._paused.is_set():
            self.pause_label = 'Pause'
            self._paused.clear()
        else:
            self.pause_label = 'Unpause'
            self._paused.set()

    def _continue_button_fired(self):
        self._paused.clear()
        self.display_value = 0
        self.current_value = 0
        self.pause_label = 'Pause'
        self._evt.set()

    def start(self, block=True):
        self.start_enabled = False
        self.pause_enabled = True
        self.continue_enabled = True

        self.current_value = self.max_value
        self._evt = Event()
        self._paused = Event()

        self._thread = Thread(target=self.run)
        self._thread.start()
        if block:
            self._thread.join()

    def run(self):
        st = time.time()
        period = 0.1
        while 1:
            if self._evt.is_set():
                break

            if self._paused.is_set():
                continue

            time.sleep(period)

            cv = self.current_value - period
            if cv <= 0:
                GUI.invoke_later(self.trait_set,
                                 current_value=0,
                                 display_value=0)
                break

            GUI.invoke_later(self.trait_set,
                             current_value=cv,
                             display_value=round(cv, 0))

        self.start_enabled = True
        self.pause_enabled = False
        self.continue_enabled = False

    def traits_view(self):
        return View(HGroup(UItem('display_value',
                                 format_str='%0.3f',
                                 editor=LEDEditor()),
                           spring,
                           UItem('start_button',
                                 enabled_when='start_enabled'),
                           UItem('pause_button',
                                 editor=ButtonEditor(label_value="pause_label"),
                                 enabled_when='pause_enabled'),
                           UItem('continue_button',
                                 enabled_when='continue_enabled')),
                    width=600)


if __name__ == '__main__':
    d = Timer()
    d.max_value = 10
    d.configure_traits()
# ============= EOF =============================================
