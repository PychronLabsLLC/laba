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

from numpy import array

from bezier_curve import bezier_curve
from hardware.device import Device
from loggable import Loggable
from traits.api import List, Str, Float, Int, Bool, Array


class Switch(Loggable):
    channel = Str
    state = Bool

    def __init__(self, cfg, *args, **kw):
        super().__init__(cfg, *args, **kw)
        self.channel = str(cfg["channel"])

    def get_state_value(self, state):
        return self.config("open_value", 1) if state else self.config("close_value", 0)


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
        self.ramp_period = cfg["ramp"].get("period", 1)
        self.nsteps = cfg["ramp"].get("nsteps", 10)
        ocpts = cfg["ramp"]["open"].get("control_points", [])
        ccpts = cfg["ramp"]["close"].get("control_points", [])
        self.degree = len(ocpts) - 1
        self.open_nodes = array([p.split(",") for p in ocpts], dtype=float)
        self.close_nodes = array([p.split(",") for p in ccpts], dtype=float)

        self.max_value = self.open_nodes[1].max()
        self.min_value = self.close_nodes[1].min()

    def ramp_max(self):
        return self.open_nodes.max()

    def ramp(self, state):
        nodes = self.open_nodes if state else self.close_nodes

        xs, ys = bezier_curve(nodes, self.nsteps + 1)
        for yi in ys:
            yield yi

        # curve = bezier.Curve(nodes, degree=self.degree)
        # ma = nodes.max()
        # for j, i in enumerate(linspace(0.0, 1.0, self.nsteps + 1)):
        #     if not j:
        #         # skip first because we already are at this value
        #         continue
        #
        #     curve2 = bezier.Curve([[i, i], [0, ma]], degree=1)
        #     intersections = curve.intersect(curve2)
        #     output = curve.evaluate_multi(intersections[0, :])[1][0]
        #     yield output


class SwitchController(Device):
    switches = List
    canvas = None

    def __init__(self, cfg, *args, **kw):
        super().__init__(cfg, *args, **kw)
        self._load_switches(cfg["switches"])

    def _load_switches(self, sws):
        for sw in sws:
            self.debug(f"loading switch {sw}")
            if sw.get("ramp"):
                klass = RampSwitch
            else:
                klass = Switch
            self.switches.append(klass(sw))

    def get_switch(self, name):
        self.debug(f"get {name}")
        return next((s for s in self.switches if s.name == name), None)

    def toggle_switch(self, name):
        s = self.get_switch(name)
        if s:
            if s.state:
                self.close_switch(name)
                return "closed"
            else:
                self.open_switch(name)
                return "open"

    def open_switch(self, name, slow=False, block=False):
        return self._actuate_switch(name, True, slow, block)

    def close_switch(self, name, slow=False, block=False):
        return self._actuate_switch(name, False, slow, block)

    def cancel_ramp(self):
        self.debug("canceling ramp")
        self._cancel_ramp.set()

    def _actuate_switch(self, name, state, slow, block):
        self.debug(f"actuate switch {name} state={state} block={block}")
        s = self.get_switch(name)
        if s:
            if slow:
                self._ramp_channel(s, state, block)
            else:
                state = s.get_state_value(state)
                self._actuate_channel(s, state)
        else:
            return f"invalid switch={name}"

    def _ramp_channel(self, s, state, block):
        self.debug(f"ramp switch {s} state={state} block={block}")
        self._cancel_ramp = Event()

        def ramp():
            print("ramp", self.canvas)
            if self.canvas:
                self.canvas.set_switch_state(s.name, "moving")

            st = time.time()
            max_time = s.nsteps * s.ramp_period * 1.1
            max_voltage = s.ramp_max() * 1.1
            self.update = {"clear": True, "datastream": "ramp", "switch_name": s.name}

            for i, si in enumerate(s.ramp(state)):
                if self._cancel_ramp.is_set():
                    break
                if i:
                    time.sleep(s.ramp_period)

                self.debug(f"set output {si}")
                self.driver.set_voltage(s.channel, si)

                if self.canvas:
                    self.canvas.set_switch_voltage(s.name, si)

                self.update = {
                    "voltage": si,
                    "relative_time_seconds": time.time() - st,
                    "max_time": max_time,
                    "max_voltage": max_voltage,
                    "value": si,
                    "datastream": "ramp",
                    "switch_name": s.name,
                }

                # time.sleep(s.ramp_period)

            s.state = state
            if self.canvas:
                self.canvas.set_switch_state(s.name, state)

        if block:
            ramp()
        else:
            self._ramp_thread = Thread(target=ramp)
            self._ramp_thread.start()

    def _actuate_channel(self, switch, state):
        channel = switch.channel
        v = switch.max_value if state else switch.min_value
        self.debug(f"actuate channel {channel} state={state}, voltage={v}")
        self.driver.actuate_channel(channel, v)

        switch.state = state
        if self.canvas:
            self.canvas.set_switch_state(switch.name, state)
            self.canvas.set_switch_voltage(switch.name, v)


# ============= EOF =============================================
