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
import csv
import time
from pathlib import Path
from threading import Thread, Event

from numpy import array

from bezier_curve import bezier_curve
from hardware.device import Device
from loggable import Loggable
from traits.api import List, Str, Float, Int, Bool, Array

from paths import paths, Paths


class Switch(Loggable):
    channel = Str
    state = Bool

    def __init__(self, cfg, *args, **kw):
        super().__init__(cfg, *args, **kw)
        self.channel = str(cfg["channel"])

    def get_state_value(self, state):
        ret = state
        if isinstance(state, bool):
            ret = (
                self.config("open_value", 1) if state else self.config("close_value", 0)
            )

        return ret


class RampSwitch(Switch):
    ramp_period = Float
    min_value = Float
    max_value = Float
    # control_points = List
    # nsteps = Int
    # open_nodes = Array
    # close_nodes = Array

    # def __init__(self, cfg, *args, **kw):
    #     super().__init__(cfg, *args, **kw)
    #     self.ramp_period = cfg["ramp"].get("period", 1)
    #     self.nsteps = cfg["ramp"].get("nsteps", 10)
    #     ocpts = cfg["ramp"]["open"].get("control_points", [])
    #     ccpts = cfg["ramp"]["close"].get("control_points", [])
    #     self.degree = len(ocpts) - 1
    #     self.open_nodes = array([p.split(",") for p in ocpts], dtype=float)
    #     self.close_nodes = array([p.split(",") for p in ccpts], dtype=float)
    #
    #     self.max_value = self.open_nodes[1].max()
    #     self.min_value = self.close_nodes[1].min()

    # def ramp_max(self):
    #     return self.open_nodes.max()
    #
    # def ramp(self, state):
    #     nodes = self.open_nodes if state else self.close_nodes
    #
    #     xs, ys = bezier_curve(nodes, self.nsteps + 1)
    #     for yi in ys:
    #         yield yi

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
                self._script_channel(s, state, slow, block)
            else:
                self._actuate_channel(s, state)
        else:
            return f"invalid switch={name}"

    def _script_channel(self, s, state, slow, block):
        self.debug(f"ramp switch {s} state={state} slow={slow}, block={block}")
        self._cancel_ramp = Event()

        # def ramp():
        #     print("ramp", self.canvas)
        #     if self.canvas:
        #         self.canvas.set_switch_state(s.name, "moving")
        #
        #     st = time.time()
        #     max_time = s.nsteps * s.ramp_period * 1.1
        #     max_voltage = s.ramp_max() * 1.1
        #     self.update = {"clear": True, "datastream": "ramp", "switch_name": s.name}
        #
        #     for i, si in enumerate(s.ramp(state)):
        #         if self._cancel_ramp.is_set():
        #             break
        #         if i:
        #             time.sleep(s.ramp_period)
        #
        #         self.debug(f"set output {si}")
        #         self.driver.set_voltage(s.channel, si)
        #
        #         if self.canvas:
        #             self.canvas.set_switch_voltage(s.name, si)
        #
        #         self.update = {
        #             "voltage": si,
        #             "relative_time_seconds": time.time() - st,
        #             "max_time": max_time,
        #             "max_voltage": max_voltage,
        #             "value": si,
        #             "datastream": "ramp",
        #             "switch_name": s.name,
        #         }
        #
        #         # time.sleep(s.ramp_period)
        #
        #     s.state = state
        #     if self.canvas:
        #         self.canvas.set_switch_state(s.name, state)
        def script():
            scriptname = "default"
            dry = True
            if isinstance(slow, str):
                scriptname = slow
                dry = False

            st = time.time()
            with open(Path(paths.curves_dir, f"{scriptname}_output.csv"), "w") as wfile:
                writer = csv.writer(wfile, delimiter=",")
                writer.writerow(["step", "time", "stepidx", "output", "voltage"])
                for idx, row in enumerate(self._load_ramp_script(scriptname)):
                    self._execute_script_row(writer, idx, row, s, st, dry=dry)

        if block:
            script()
        else:
            self._ramp_thread = Thread(target=script)
            self._ramp_thread.start()

    def _load_ramp_script(self, name):
        p = Path(paths.curves_dir, f"{name}.csv")
        with open(p, "r") as rfile:
            reader = csv.reader(rfile, delimiter=",")
            rows = [row for row in reader]
            for row in rows[1:]:
                yield row

    def _execute_script_row(self, writer, idx, row, s, st, dry):
        self.debug(f"execute script row. line={idx+1}, {row}")
        voltage, n_steps, dwell_time, curve = row[:4]
        voltage = float(voltage)
        n_steps = int(n_steps)
        dwell_time = float(dwell_time)
        curve = int(curve)

        self.debug(f"set output {voltage}")

        def make_curve(curve_name, nsteps=100, invert=False):
            curve_path = Path(paths.curves_dir, f"curve_rates.csv")
            with open(curve_path, "r") as rfile:
                reader = csv.reader(rfile, delimiter=",")
                rows = [row for row in reader]
                control_points = rows[curve_name - 1]
                self.debug(f"using control points {control_points}")
                n = len(control_points) + 1
                control_points = [
                    ((i + 1) / n, float(cp) / 100)
                    for i, cp in enumerate(control_points)
                ]
                control_points.insert(0, (0, 0))
                control_points.append((1, 1))
                xs, ys = bezier_curve(control_points, nsteps + 1)
                if invert:
                    ys = [1 - yi for yi in ys]
                return ys[:-1]

        for stepidx, out in enumerate(make_curve(curve, n_steps)):
            vi = voltage * out
            self.debug(f"set output {out}, voltage={vi}")
            ct = time.time() - st
            kw = {"relative_time_seconds": ct, "max_voltage": 7}

            self._set_voltage(s, vi, **kw)
            if not dry:
                time.sleep(1)

            writer.writerow([idx, ct, stepidx, out, vi])

        if dwell_time and not dry:
            self.debug(f"dwelling {dwell_time}s")
            time.sleep(dwell_time)

    def _set_voltage(self, s, voltage, **kw):
        self.driver.set_voltage(s.channel, voltage)
        if self.canvas:
            self.canvas.set_switch_voltage(s.name, voltage)

        self.update = {
            "voltage": voltage,
            "value": voltage,
            "datastream": "ramp",
            "switch_name": s.name,
            **kw,
        }

    def _actuate_channel(self, switch, state):
        channel = switch.channel

        v = switch.get_state_value(state)

        self.debug(f"actuate channel {channel} state={state}, voltage={v}")
        self.driver.actuate_channel(channel, v)

        switch.state = state
        if self.canvas:
            self.canvas.set_switch_state(switch.name, state)
            self.canvas.set_switch_voltage(switch.name, v)


# ============= EOF =============================================
