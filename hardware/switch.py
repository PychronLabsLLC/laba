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
from traits.api import List, Str, Float, Int, Bool, Array


class Switch(Loggable):
    channel = Str
    state = Bool

    def __init__(self, cfg, *args, **kw):
        super().__init__(cfg, *args, **kw)
        self.channel = str(cfg['channel'])


class RampSwitch(Switch):
    ramp_period = Float
    min_value = Float
    max_value = Float
    # control_points = List
    nsteps = Int
    open_nodes = Array
    close_nodes = Array

    def __init__(self, cfg, *args, **kw):
        super().__init__(cfg, *args, **kw)
        self.ramp_period = cfg['ramp'].get('period', 1)
        self.nsteps = cfg['ramp'].get('nsteps', 10)
        ocpts = cfg['ramp']['open'].get('control_points', [])
        ccpts = cfg['ramp']['close'].get('control_points', [])
        self.degree = len(ocpts)-1
        self.open_nodes = array([p.split(",") for p in ocpts], dtype=float).T
        self.close_nodes = array([p.split(",") for p in ccpts], dtype=float).T

    def ramp_max(self):
        return self.open_nodes.max()

    def ramp(self, state):
        # nodes = array([p.split(",") for p in self.control_points], dtype=float).T
        nodes = self.open_nodes if state else self.close_nodes
        curve = bezier.Curve(nodes, degree=self.degree)
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
        self.debug(f'get {name}')
        return next((s for s in self.switches if s.name == name), None)

    def toggle_switch(self, name):
        s = self.get_switch(name)
        if s:
            if s.state:
                self.close_switch(name)
                return 'closed'
            else:
                self.open_switch(name)
                return 'open'

    def open_switch(self, name, slow=False, block=False):
        return self._actuate_switch(name, True, slow, block)

    def close_switch(self, name, slow=False, block=False):
        return self._actuate_switch(name, False, slow, block)

    def cancel_ramp(self):
        self.debug('canceling ramp')
        self._cancel_ramp.set()

    def _actuate_switch(self, name, state, slow, block):
        self.debug(f'actuate switch {name} state={state} block={block}')
        s = self.get_switch(name)
        if s:
            if slow:
                self._ramp_channel(s, state, block)
            else:
                self._actuate_channel(s, state)
        else:
            return f'invalid switch={name}'

    def _ramp_channel(self, s, state, block):
        self.debug(f'ramp switch {s} state={state} block={block}')
        self._cancel_ramp = Event()

        def ramp():
            self.canvas.set_switch_state(s.name, 'moving')
            st = time.time()
            max_time = s.nsteps * s.ramp_period * 1.1
            max_voltage = s.ramp_max()*1.1
            self.update = {'clear': True,
                           'datastream': 'ramp'}

            for i, si in enumerate(s.ramp(state)):
                if self._cancel_ramp.is_set():
                    break
                if i:
                    time.sleep(s.ramp_period)

                self.debug(f'set output {si}')
                self.driver.set_voltage(s.channel, si)

                self.canvas.set_switch_voltage(s.name, si)
                self.update = {'voltage': si,
                               'relative_time_seconds': time.time() - st,
                               'max_time': max_time,
                               'max_voltage': max_voltage,
                               'value': si,
                               'datastream': 'ramp'
                               }

                # time.sleep(s.ramp_period)

            s.state = state
            self.canvas.set_switch_state(s.name, state)

        if block:
            ramp()
        else:

            self._ramp_thread = Thread(target=ramp)
            self._ramp_thread.start()

    def _actuate_channel(self, switch, state):
        channel = switch.channel

        self.debug(f'actuate channel {channel} state={state}')
        self.driver.actuate_channel(channel, state)

        switch.state = state
        self.canvas.set_switch_state(switch.name, state)

# ============= EOF =============================================
