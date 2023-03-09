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

import bezier
from numpy import array, linspace

from hardware.device import Device
from loggable import Loggable
from traits.api import List, Str, Float, Int


class Switch(Loggable):
    channel = Str

    def __init__(self, cfg, *args, **kw):
        super().__init__(cfg, *args, **kw)
        self.channel = str(cfg['channel'])


class RampSwitch(Switch):
    ramp_period = Float
    min_value = Float
    max_value = Float
    control_points = List
    nsteps = Int

    def __init__(self, cfg, *args, **kw):
        super().__init__(cfg, *args, **kw)
        self.ramp_period = cfg['ramp'].get('period', 1)
        self.nsteps = cfg['ramp'].get('nsteps', 10)
        self.control_points = cfg['ramp'].get('control_points', [])

    def ramp(self):
        nodes = array([p.split(",") for p in self.control_points], dtype=float).T
        curve = bezier.Curve(nodes, degree=len(self.control_points)-1)
        ma = nodes.max()

        for i in linspace(0.0, 1.0, self.nsteps):
            curve2 = bezier.Curve([[i, i], [0, ma]], degree=1)
            intersections = curve.intersect(curve2)
            output = curve.evaluate_multi(intersections[0, :])[1][0]
            yield output


class SwitchController(Device):
    switches = List

    def __init__(self, cfg, *args, **kw):
        super().__init__(cfg, *args, **kw)
        self._load_switches(cfg['switches'])

    def _load_switches(self, sws):
        for sw in sws:
            self.debug(f'loading switch {sw}')
            if sw.get('ramp'):
                klass = RampSwitch
            else:
                klass = Switch
            self.switches.append(klass(sw))

    def get_switch(self, name):
        return next((s for s in self.switches if s.name == name))

    def open_switch(self, name, slow=False):
        self._actuate_switch(name, True, slow)

    def close_switch(self, name, slow=False):
        self._actuate_switch(name, False, slow)

    def cancel_ramp(self):
        self.debug('canceling ramp')
        self._cancel_ramp.set()

    def _actuate_switch(self, name, state, slow):
        self.debug(f'actuate switch {name} state={state}')
        s = self.get_switch(name)
        if slow:
            self._ramp_channel(s, state)
        else:
            self._actuate_channel(s.channel, state, slow)

    def _ramp_channel(self, s, state):
        self.debug(f'ramp switch {s} state={state}')

        def ramp():
            for si in s.ramp():
                if self._cancel_ramp.is_set():
                    break

                self.debug(f'set output {si}')
                time.sleep(s.ramp_period)

        self._cancel_ramp = Event()
        self._ramp_thread = Thread(target=ramp)
        self._ramp_thread.start()

    def _actuate_channel(self, channel, state, slow):
        self.debug(f'actuate channel {channel} state={state}')

# ============= EOF =============================================
