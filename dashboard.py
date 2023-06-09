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

from chaco.data_view import DataView
from enable.component_editor import ComponentEditor
from enable.container import Container
from numpy import array
from traits.has_traits import on_trait_change
from traitsui.group import VSplit
from traitsui.qt4.extra.led_editor import LEDEditor

from automation import Automation
from canvas.elements import (
    CanvasOverlay,
    CanvasSwitch,
    CanvasConnection,
    CanvasTank,
    CanvasRampSwitch,
)
from canvas.network import CanvasNetwork
from canvas.tools import CanvasInteractor
from db.db import DBClient
from figure import Figure
from hardware.device import Device
from loggable import Loggable
from traits.api import Instance, Button, Bool, Float, List, Str
from traitsui.api import View, UItem, VGroup, HGroup, spring, Item, EnumEditor, HSplit

from paths import paths
from util import yload


class Card(Loggable):
    def __init__(self, application, *args, **kw):
        super().__init__(*args, **kw)
        self.application = application

    def traits_view(self):
        name = self.get_name()
        v = View(VGroup(*self.make_view(), show_border=True, label=name))
        return v

    def make_view(self):
        raise NotImplementedError

    def get_name(self):
        return self.name


class DeviceCard(Card):
    device_functions = List
    devices = List

    def __init__(self, application, cfg, *args, **kw):
        super().__init__(cfg, *args, **kw)
        dfs = []
        dvs = []
        for dev in cfg.get("devices", []):
            dd = application.get_service(Device, f"name=='{dev['name']}'")
            dvs.append(dd)
            func = dev.get("function", {"name": "get_value"})
            print(dd, func)
            if func:
                aa = func.get("args", ())
                kk = func.get("kwargs", {})
                name = func.get("name", "get_value")

            dfs.append((getattr(dd, name), aa, kk))

        self.devices = dvs
        self.device_functions = dfs


class Canvas(Card):
    container = Instance(Container)

    def __init__(self, application, cfg, *args, **kw):
        self._cfg = cfg["elements"]
        super().__init__(application, cfg, *args, **kw)
        self.render()

    def get_switch(self, name):
        return next(
            (
                o
                for o in self.container.overlays
                if hasattr(o, "name") and o.name == name
            )
        )

    def set_switch_voltage(self, name, si):
        o = self.get_switch(name)
        o.voltage = si
        o.request_redraw()

    def set_switch_state(self, name, state):
        o = self.get_switch(name)
        if isinstance(state, bool):
            state = "open" if state else "closed"
        o.state = state

        self.network.update(name)
        o.request_redraw()

    def render(self):
        self.container = dv = DataView()
        dv.aspect_ratio = 1
        dv.index_range.low = 0
        dv.index_range.high = 100
        dv.value_range.low = 0
        dv.value_range.high = 100

        dv.index_range.low = -50
        dv.index_range.high = 50
        dv.value_range.low = -50
        dv.value_range.high = 50

        controller = self.application.get_service(Device, f"name=='switch_controller'")
        tool = CanvasInteractor(component=dv, controller=controller)

        controller.canvas = self

        self.container.tools.append(tool)
        cv = CanvasOverlay(component=dv)
        dv.overlays.append(cv)

        connections = []
        for ei in self._cfg:
            t = ei.get("translate", {"x": 0, "y": 0})
            d = ei.get("dimension", {"w": 5, "h": 5})
            kind = ei.get("kind", "CanvasSwitch")
            kw = {}
            if kind == "CanvasSwitch":
                klass = CanvasSwitch
            elif kind == "CanvasRampSwitch":
                klass = CanvasRampSwitch
            elif kind == "CanvasTank":
                klass = CanvasTank
                dc = ei.get("default_color", "0.75,0.25,0.5")
                if "," in dc:
                    dc = [float(c) for c in dc.split(",")]
                kw = {"precedence": ei.get("precedence", 1), "default_color": dc}
            elif kind == "Connection":
                # load all elements before loading any connections
                connections.append(ei)
                continue

            vv = klass(
                **kw,
                component=dv,
                x=t["x"],
                y=t["y"],
                name=ei["name"],
                width=d["w"],
                height=d["h"],
            )
            dv.overlays.append(vv)

        for ci in connections:
            start = next((o for o in dv.overlays if o.name == ci["start"]["name"]))
            end = next((o for o in dv.overlays if o.name == ci["end"]["name"]))
            c = CanvasConnection(component=dv, start=start, end=end)
            dv.underlays.append(c)

        self.network = CanvasNetwork(dv)

        for s in controller.switches:
            self.set_switch_state(s.name, s.state)
            self.network.update(s.name)

        dv.padding = 0
        dv.bgcolor = "orange"

    def make_view(self):
        return (
            UItem(
                "container",
                editor=ComponentEditor(height=800),
                # height=0.75
            ),
        )


class BaseScan(DeviceCard):
    active = Bool(False)
    period = Float(1)

    _scan_evt = None

    def __init__(self, application, cfg, *args, **kw):
        super().__init__(application, cfg, *args, **kw)
        self.period = cfg.get("period", 1.0)

    def _scan(self):
        if self.active:
            self._scan_evt.set()
            return
        else:
            self._scan_evt = Event()
            self.active = True

        sp = self.period

        def _scan():
            st = time.time()

            for d in self.devices:
                d.update = {"clear": True, "datastream": "scan"}

            while not self._scan_evt.is_set():
                for i, (df, args, kw) in enumerate(self.device_functions):
                    kw["datastream"] = "scan"
                    self._scan_hook(i, df, st, args, kw)
                # time.sleep(sp)
                self._scan_evt.wait(sp)

            self.active = False

        t = Thread(target=_scan, daemon=True)
        self._scan_thread = t
        self._scan_thread.start()

    def _scan_hook(self, i, df, st, args, kw):
        pass


class Scan(BaseScan):
    figure = Instance(Figure, ())
    start_button = Button("Start")
    stop_button = Button("Stop")
    start_enabled = Bool(True)

    def _stop_button_fired(self):
        self.start_enabled = True
        self._scan_evt.set()

    def _start_button_fired(self):
        self.start_enabled = False
        self.figure.clear_data("s0")
        self._scan()

    def _scan_hook(self, i, df, st, args, kw):
        self.figure.add_datum(f"s{i}", time.time() - st, df(*args, **kw))

    def _figure_default(self):
        f = Figure()
        f.new_plot(
            xtitle="Time(s)",
            ytitle="Valve",
            padding_left=50,
            padding_bottom=50,
            padding_top=20,
            padding_right=20,
        )
        f.new_series("s0")
        f.set_x_limits(0, 5)

        return f

    def make_view(self):
        return (
            HGroup(
                spring,
                UItem("start_button", enabled_when="start_enabled"),
                UItem("stop_button", enabled_when="not start_enabled"),
            ),
            UItem("figure", style="custom"),
        )


class LEDReadOut(BaseScan):
    value = Float

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._scan()

    def _scan_hook(self, i, df, st, args, kw):
        self.value = df(*args, **kw)

    def make_view(self):
        return (Item("value", label=self.name, editor=LEDEditor()),)


class Switch(DeviceCard):
    open_button = Button("Open")
    close_button = Button("Close")
    state = Bool
    device = Instance(Device)

    def __init__(self, application, cfg, *args, **kw):
        super().__init__(application, cfg, *args, **kw)
        self.switch_name = cfg["switch"]["name"]
        self.device = self.devices[0]

    def _open_button_fired(self):
        dev = self.devices[0]
        dev.open_switch(self.switch_name)
        self.state = True

    def _close_button_fired(self):
        dev = self.devices[0]
        dev.close_switch(self.switch_name)
        self.state = False

    def make_view(self):
        return (
            HGroup(
                UItem("open_button"),
                UItem("close_button"),
                Item("state", style="readonly", label="State"),
            ),
        )

    def get_name(self):
        return f"{self.name} ({self.switch_name})"


class EMSwitch(Switch):
    slow_open_button = Button("Slow Open")
    slow_close_button = Button("Slow Close")
    figure = Instance(Figure)

    def _figure_default(self):
        fig = Figure()
        p = fig.new_plot(
            padding_left=50, padding_bottom=50, padding_top=20, padding_right=20
        )
        p.x_axis.title = "Time (s)"
        p.y_axis.title = "Voltage (V)"
        fig.new_series("vt", type="line")
        p.index_range.low = 0
        p.index_range.high = 60

        p.value_range.low = 0
        p.value_range.high = 10

        return fig

    def _slow_close_button_fired(self):
        dev = self.device
        dev.close_switch(self.switch_name, slow=True)
        self.state = False

    def _slow_open_button_fired(self):
        dev = self.device
        dev.open_switch(self.switch_name, slow=True)
        self.state = True

    @on_trait_change("device:update")
    def _handle_device_update(self, new):
        if new:
            if new["switch_name"] != self.switch_name:
                return

            if new.get("clear"):
                self.figure.clear_data("vt")
            else:
                self.figure.add_datum(
                    "vt", new["relative_time_seconds"], new["voltage"]
                )
                self.figure.set_x_limits(-1, new["max_time"])
                self.figure.set_y_limits(-1, new["max_voltage"])

    def make_view(self):
        return (
            VGroup(
                HGroup(
                    UItem("open_button"),
                    UItem("close_button"),
                    spring,
                    UItem("slow_open_button"),
                    UItem("slow_close_button"),
                    Item("state", style="readonly", label="State"),
                ),
                UItem("figure", style="custom"),
            ),
        )


class Procedures(Card):
    start_button = Button("Start")
    stop_button = Button("Stop")
    script_name = Str
    names = List

    automation = Instance(Automation)

    def __init__(self, application, cfg, *args, **kw):
        super().__init__(application, cfg=cfg, *args, **kw)
        yobj = yload(paths.automations_path)
        names = [a["name"] for a in yobj]
        # self.application = application
        self.names = names

    def make_view(self):
        return (
            HGroup(
                UItem("script_name", editor=EnumEditor(name="names")),
                UItem("start_button"),
                UItem("stop_button"),
            ),
        )

    def _start_button_fired(self):
        # with open(paths.automations_path, 'r') as rfile:
        #     yobj = yaml.load(rfile, yaml.SafeLoader)

        yobj = yload(paths.automations_path)
        for automation in yobj:
            if automation["name"] == self.script_name:
                a = Automation(
                    {
                        "name": self.script_name,
                        "path": paths.get_automation_path(automation["path"]),
                    },
                    application=self.application,
                )

                self.automation = a
                self.automation.run()

    def _stop_button_fired(self):
        if self.automation:
            self.automation.cancel()


class BaseDashboard(Loggable):
    pass


class HistoryDashboard(BaseDashboard):
    device_name = Str
    device_names = List
    figure = Instance(Figure)

    datastream_name = Str
    datastream_names = List

    def __init__(self, application, *args, **kw):
        super().__init__(*args, **kw)
        self.application = application
        ds = application.get_services(Device)
        self.device_names = [d.name for d in ds]
        self.figure = Figure()
        self.figure.new_plot()
        self.figure.new_series("default")
        # self.dbclient = DBClient()

    def _device_name_changed(self, new):
        if new:
            dbclient = DBClient()
            with dbclient.session() as sess:
                ds = dbclient.get_datastream_names(new, sess=sess)

                self.datastream_names = ds

                self.datastream_name = ""
                self.datastream_name = ds[0]

    def _datastream_name_changed(self, new):
        if new:
            dbclient = DBClient()
            with dbclient.session() as sess:
                dbdev = dbclient.get_datastream(new, self.device_name, sess=sess)
                if ms := dbdev.measurements:
                    x, y = zip(*[(mi.timestamp.timestamp(), mi.value) for mi in ms])
                    x = array(x)
                    x -= x.min()
                    self.figure.new_series("default", xdata=x, ydata=y)
        else:
            self.figure.clear_data("default")

    def traits_view(self):
        cgrp = VGroup(
            HGroup(
                Item("device_name", editor=EnumEditor(name="device_names")),
                Item("datastream_name", editor=EnumEditor(name="datastream_names")),
            )
        )
        fgrp = VGroup(UItem("figure", style="custom"))
        return View(VGroup(cgrp, fgrp))


class Dashboard(BaseDashboard):
    def __init__(self, application, cfg, *args, **kw):
        super().__init__(cards=cfg["cards"], *args, **kw)
        self.application = application

    def traits_view(self):
        return View(self._build_dashboard_elements())

    def _build_dashboard_elements(self):
        ga = []
        gb = []
        gahs = []
        gbhs = []
        for i, c in enumerate(self.cards):
            kind = c["kind"]
            factory = globals().get(kind)
            card = factory(self.application, c)
            height = c.get("height", 0.5)
            self.add_trait(c["name"], card)
            item = UItem(c["name"], style="custom", height=height)
            if i % 2:
                gbhs.append(height)
                gb.append(item)
            else:
                gahs.append(height)
                ga.append(item)

        for gs, hs in ((ga, gahs), (gb, gbhs)):
            s = sum(hs)
            for gi in gs:
                gi.height /= s

        return HSplit(VSplit(*ga), VSplit(*gb))

    # def traits_view(self):
    #     v = View(self._build_dashboard_elements())
    #     return v


# ============= EOF =============================================
