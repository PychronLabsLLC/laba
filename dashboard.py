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
import math
import time
from threading import Thread, Event

import yaml
from chaco.array_plot_data import ArrayPlotData
from chaco.data_view import DataView
from chaco.plot import Plot
from chaco.plot_containers import VPlotContainer
from enable.component_editor import ComponentEditor
from enable.container import Container
from numpy import hstack
from traits.has_traits import on_trait_change
from traitsui.group import VSplit
from traitsui.qt4.extra.led_editor import LEDEditor

from automation import Automation
from canvas.elements import CanvasOverlay, CanvasSwitch
from canvas.tools import CanvasInteractor
from hardware.device import Device
from loggable import Loggable
from traits.api import Instance, Button, Bool, Float, List, Str
from traitsui.api import View, UItem, VGroup, HGroup, spring, Item, EnumEditor, HSplit

from paths import paths


class Figure(Loggable):
    plotcontainer = Instance(VPlotContainer, ())

    def new_plot(self, xtitle=None, ytitle=None, **kw):
        p = Plot(data=ArrayPlotData(), **kw)

        if xtitle:
            p.x_axis.title = xtitle
        if ytitle:
            p.y_axis.title = ytitle

        self.plotcontainer.add(p)

        return p

    def new_series(self, name, plotid=0, type='line', **kw):
        plot = self.get_plot(plotid)
        plot.data.set_data('x0', [])
        plot.data.set_data('y0', [])
        plot.plot(('x0', 'y0'), name=name, type=type, **kw)

    def add_datum(self, name, x, y, plotid=0):
        series = self.get_series(name, plotid)

        xx = hstack((x, series.index.get_data()))
        series.index.set_data(xx)

        series.value.set_data(hstack((y, series.value.get_data())))
        plot = self.get_plot(plotid)
        l = plot.index_range.low
        h = plot.index_range.high

        if x >= h:
            lx = len(xx)
            if lx > 2:
                step = math.ceil((xx[0] - xx[-1]) / lx)
        # step = 0
        # if x > (h * 0.95):
        #     lx = len(xx)
        #     if lx > 2 and not step:
        #         step = math.ceil((xx[0] - xx[-1]) / lx)
        #
            self.set_x_limits(l + step, h + step, plotid)

    def clear_data(self, name, plotid=0):
        series = self.get_series(name, plotid)
        series.index.set_data([])
        series.value.set_data([])

    def get_series(self, name, plotid=0):
        plot = self.get_plot(plotid)
        return plot.plots[name][0]

    def get_plot(self, idx):
        return self.plotcontainer.components[idx]

    def set_x_limits(self, l, h, idx=0):
        plot = self.get_plot(idx)
        plot.index_range.low = l
        plot.index_range.high = h

    def set_y_limits(self, l, h, idx=0):
        plot = self.get_plot(idx)
        plot.value_range.low = l
        plot.value_range.high = h

    def traits_view(self):
        v = View(
            UItem('plotcontainer', editor=ComponentEditor()))
        return v


class Card(Loggable):
    def __init__(self, application, *args, **kw):
        super().__init__(*args, **kw)
        self.application = application

    def traits_view(self):
        v = View(VGroup(*self.make_view(),
                        show_border=True,
                        label=self.name))
        return v

    def make_view(self):
        raise NotImplementedError


class DeviceCard(Card):
    device_functions = List
    devices = List

    def __init__(self, application, cfg, *args, **kw):
        super().__init__(cfg, *args, **kw)
        dfs = []
        dvs = []
        for dev in cfg.get('devices', []):
            dd = application.get_service(Device, f"name=='{dev['name']}'")
            dvs.append(dd)
            func = dev.get('function')
            if func:
                dfs.append(getattr(dd, func))

        self.devices = dvs
        self.device_functions = dfs


class Canvas(Card):
    container = Instance(Container)

    def __init__(self, application, cfg, *args, **kw):
        self._cfg = cfg['elements']
        super().__init__(application, cfg, *args, **kw)
        self.render()

    def get_switch(self, name):
        return next((o for o in self.container.overlays
                     if hasattr(o, 'name') and o.name == name))

    def set_switch_voltage(self, name, si):
        o = self.get_switch(name)
        o.voltage = si
        o.request_redraw()

    def set_switch_state(self, name, state):
        o = self.get_switch(name)
        if isinstance(state, bool):
            state = 'open' if state else 'closed'
        o.state = state
        o.request_redraw()

    def render(self):
        self.container = dv = DataView()
        # dv.aspect_ratio = 1
        dv.index_range.low = 0
        dv.index_range.high = 100
        dv.value_range.low = 0
        dv.value_range.high = 100

        dv.index_range.low = -50
        dv.index_range.high = 50
        dv.value_range.low = -50
        dv.value_range.high = 50

        controller = self.application.get_service(Device, f"name=='switch_controller'")
        tool = CanvasInteractor(component=dv,
                                controller=controller)

        controller.canvas = self

        self.container.tools.append(tool)
        cv = CanvasOverlay(component=dv)
        dv.overlays.append(cv)

        for ei in self._cfg:
            t = ei.get('translate', {'x': 0, 'y': 0})
            d = ei.get('dimension', {'w': 5, 'h': 5})
            vv = CanvasSwitch(component=dv, x=t['x'], y=t['y'],
                              name=ei['name'],
                              width=d['w'],
                              height=d['h'])
            dv.overlays.append(vv)

        dv.padding = 0
        dv.bgcolor = 'orange'

    def make_view(self):
        return UItem('container', editor=ComponentEditor()),


class BaseScan(DeviceCard):
    active = Bool(False)
    period = Float(1)

    _scan_evt = None

    def __init__(self, application, cfg, *args, **kw):
        super().__init__(application, cfg, *args, **kw)
        self.period = cfg.get('period', 1.0)

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
            while not self._scan_evt.is_set():
                for i, df in enumerate(self.device_functions):
                    self._scan_hook(i, df, st)
                time.sleep(sp)

            self.active = False

        t = Thread(target=_scan)
        self._scan_thread = t
        self._scan_thread.start()

    def _scan_hook(self, i, df, st):
        pass


class Scan(BaseScan):
    figure = Instance(Figure, ())
    start_button = Button('Start')

    def _start_button_fired(self):
        self.figure.clear_data('s0')
        self._scan()

    def _scan_hook(self, i, df, st):
        self.figure.add_datum(f's{i}', time.time() - st, df())

    def _figure_default(self):
        f = Figure()
        f.new_plot(xtitle='Time(s)', ytitle='Valve',
                   padding_left=50, padding_bottom=50, padding_top=20, padding_right=20)
        f.new_series('s0')
        f.set_x_limits(0, 5)

        return f

    def make_view(self):
        return HGroup(spring, UItem('start_button')), UItem('figure', style='custom'),


class LEDReadOut(BaseScan):
    value = Float

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._scan()

    def _scan_hook(self, i, df, st):
        self.value = df()

    def make_view(self):
        return Item('value',
                    label=self.name,
                    editor=LEDEditor()),


class Switch(DeviceCard):
    open_button = Button('Open')
    close_button = Button('Close')
    state = Bool

    def __init__(self, application, cfg, *args, **kw):
        super().__init__(application, cfg, *args, **kw)
        self.switch_name = cfg['switch']['name']

    def _open_button_fired(self):
        dev = self.devices[0]
        dev.open_switch(self.switch_name)
        self.state = True

    def _close_button_fired(self):
        dev = self.devices[0]
        dev.close_switch(self.switch_name)
        self.state = False

    def make_view(self):
        return HGroup(UItem('open_button'),
                      UItem('close_button'),
                      Item('state',
                           style='readonly',
                           label='State')),


class EMSwitch(Switch):
    slow_open_button = Button('Slow Open')
    slow_close_button = Button('Slow Close')
    figure = Instance(Figure)

    def _figure_default(self):
        fig = Figure()
        p = fig.new_plot(padding_left=50, padding_bottom=50, padding_top=20, padding_right=20)
        p.x_axis.title = 'Time (s)'
        p.y_axis.title = 'Voltage (V)'
        fig.new_series('vt', type='line')
        p.index_range.low = 0
        p.index_range.high = 60

        p.value_range.low = 0
        p.value_range.high = 10

        return fig

    def _slow_close_button_fired(self):
        dev = self.devices[0]
        dev.close_switch(self.switch_name, slow=True)
        self.state = False

    def _slow_open_button_fired(self):
        dev = self.devices[0]
        dev.open_switch(self.switch_name, slow=True)
        self.state = True

    @on_trait_change('devices:update')
    def _handle_device_update(self, new):
        if new:
            if new.get('clear'):
                self.figure.clear_data('vt')
            else:
                self.figure.add_datum('vt', new['time'], new['voltage'])
                self.figure.set_x_limits(-1, new['max_time'])
                self.figure.set_y_limits(-1, new['max_voltage'])

    def make_view(self):
        return VGroup(HGroup(UItem('open_button'),
                             UItem('close_button'),
                             spring,
                             UItem('slow_open_button'),
                             UItem('slow_close_button'),

                             Item('state',
                                  style='readonly',
                                  label='State')),
                      UItem('figure', style='custom')
                      ),


class Procedures(Card):
    start_button = Button("Start")
    stop_button = Button("Stop")
    script_name = Str
    names = List

    automation = Instance(Automation)

    def __init__(self, application, cfg, *args, **kw):
        super().__init__(application, cfg=cfg, *args, **kw)
        names = []
        with open(paths.automations_path, 'r') as rfile:
            yobj = yaml.load(rfile, yaml.SafeLoader)
            for automation in yobj:
                names.append(automation['name'])

        # self.application = application
        self.names = names

    def make_view(self):
        return HGroup(UItem('script_name', editor=EnumEditor(name='names')),
                      UItem('start_button'),
                      UItem('stop_button')),

    def _start_button_fired(self):
        with open(paths.automations_path, 'r') as rfile:
            yobj = yaml.load(rfile, yaml.SafeLoader)
            for automation in yobj:
                if automation['name'] == self.script_name:
                    a = Automation({"name": self.script_name,
                                    "path": paths.get_automation_path(automation['path'])},
                                   application=self.application)

                    self.automation = a
                    self.automation.run()

    def _stop_button_fired(self):
        if self.automation:
            self.automation.cancel()


class Dashboard(Loggable):
    def __init__(self, application, cfg, *args, **kw):
        super().__init__(cards=cfg['cards'], *args, **kw)
        self.application = application

    def traits_view(self):
        return View(self._build_dashboard_elements())

    def _build_dashboard_elements(self):
        ga = []
        gb = []
        for i, c in enumerate(self.cards):
            kind = c['kind']
            factory = globals().get(kind)
            card = factory(self.application, c)

            self.add_trait(c['name'], card)
            item = UItem(c['name'], style='custom')
            if i % 2:
                gb.append(item)
            else:
                ga.append(item)

        return HSplit(VSplit(*ga), VSplit(*gb))

    # def traits_view(self):
    #     v = View(self._build_dashboard_elements())
    #     return v
# ============= EOF =============================================
