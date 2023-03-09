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
import random
import time
from threading import Thread, Event

from chaco.array_plot_data import ArrayPlotData
from chaco.base_plot_container import BasePlotContainer
from chaco.plot import Plot
from chaco.plot_containers import VPlotContainer
from enable.component_editor import ComponentEditor
from numpy import hstack

from device import Device
from loggable import Loggable
from traits.api import Instance, Button, Bool, Float, List
from traitsui.api import View, UItem, VGroup, HGroup, spring


class Figure(Loggable):
    plotcontainer = Instance(VPlotContainer, ())

    def new_plot(self, **kw):
        p = Plot(data=ArrayPlotData(), **kw)
        self.plotcontainer.add(p)

    def new_series(self, name, plotid=0):
        plot = self.get_plot(plotid)
        plot.data.set_data('x0', [])
        plot.data.set_data('y0', [])
        plot.plot(('x0', 'y0'), name=name, type='line')

    def add_datum(self, name, x, y, plotid=0):
        series = self.get_series(name, plotid)
        series.index.set_data(hstack((x, series.index.get_data())))
        series.value.set_data(hstack((y, series.value.get_data())))

    def clear_data(self, name, plotid=0):
        series = self.get_series(name, plotid)
        series.index.set_data([])
        series.value.set_data([])

    def get_series(self, name, plotid=0):
        plot = self.get_plot(plotid)
        return plot.plots[name][0]

    def get_plot(self, idx):
        return self.plotcontainer.components[idx]

    def traits_view(self):
        v = View(
            UItem('plotcontainer', editor=ComponentEditor()))
        return v


class Card(Loggable):
    device_functions = List

    def __init__(self, application, cfg, *args, **kw):
        super().__init__(*args, **kw)
        dfs =[]
        for dev in cfg['devices']:
            dd = application.get_service(Device, f"name=='{dev['name']}'")
            print(dd, dev['name'])
            dfs.append(getattr(dd, dev['function']))

        self.device_functions = dfs


class Scan(Card):
    figure = Instance(Figure, ())
    start_button = Button('Start')
    active = Bool(False)
    period = Float(1)

    _scan_evt = None

    def _start_button_fired(self):
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
                    self.figure.add_datum(f's{i}', time.time() - st, df())
                time.sleep(sp)

            self.active = False

        self.figure.clear_data('s0')
        t = Thread(target=_scan)
        self._scan_thread = t
        self._scan_thread.start()

    def _figure_default(self):
        f = Figure()
        f.new_plot()
        f.new_series('s0')

        return f

    def traits_view(self):
        return View(HGroup(spring, UItem('start_button')),
                    UItem('figure', style='custom'))


class Dashboard(Loggable):
    def __init__(self, application, cfg, *args, **kw):
        super().__init__(cards=cfg['cards'], *args, **kw)
        self.application = application

    def traits_view(self):
        return View(self._build_dashboard_elements())

    def _build_dashboard_elements(self):
        gs = []
        for c in self.cards:
            kind = c['kind']
            if kind == 'Scan':
                factory = Scan

            card = factory(self.application, c)

            self.add_trait(c['name'], card)
            gs.append(UItem(c['name'], style='custom'))

        return VGroup(*gs)

    # def traits_view(self):
    #     v = View(self._build_dashboard_elements())
    #     return v
# ============= EOF =============================================
