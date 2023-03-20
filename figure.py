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

from chaco.array_plot_data import ArrayPlotData
from chaco.plot import Plot
from chaco.plot_containers import VPlotContainer
from enable.base_tool import BaseTool
from enable.component_editor import ComponentEditor
from numpy import hstack
from traits.api import on_trait_change, Instance
from traitsui.api import View, UItem, Item, VGroup, HGroup, TextEditor, Handler

from loggable import Loggable


class Figure(Loggable):
    plotcontainer = Instance(VPlotContainer, ())

    def new_plot(self, xtitle=None, ytitle=None, **kw):
        p = Plot(data=ArrayPlotData(), **kw)

        if xtitle:
            p.x_axis.title = xtitle
        if ytitle:
            p.y_axis.title = ytitle

        t = AxisTool(component=p.y_axis)
        p.tools.append(t)
        t = AxisTool(component=p.x_axis)
        p.tools.append(t)

        self.plotcontainer.add(p)

        return p

    def new_series(self, name, plotid=0, type='line', xdata=None, ydata=None, **kw):
        if xdata is None:
            xdata = []
        if ydata is None:
            ydata = []
        plot = self.get_plot(plotid)
        plot.data.set_data('x0', xdata)
        plot.data.set_data('y0', ydata)
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
            if lx >= 2:
                step = math.ceil((xx[0] - xx[-1]) / lx)
            # if x > (h * 0.95):
            #     lx = len(xx)
            #     if lx > 2 and not step:
            #         step = math.ceil((xx[0] - xx[-1]) / lx)
            #
            self.set_x_limits(l + step, h + step, plotid)

    def clear_data(self, name=None, plotid=0):

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


class AxisTool(BaseTool):
    def normal_right_down(self, event):
        if self.hittest(event):
            # wrap_axis = WrapAxis(self.component)
            # wrap_axis.edit_traits(view=AxisView, handler=AxisViewHandler(), kind="live")
            self.component.edit_traits(view=AxisView,
                                       handler=AxisViewHandler()
                                       )
            self.component.request_redraw()
            event.handled = True

    @on_trait_change("component:+")
    def handle_change(self, name, new):
        if name.startswith("_"):
            return
        self.component.request_redraw()

    def hittest(self, event):
        return self.component.is_in(event.x, event.y)


limit_grp = VGroup(
    Item(
        "object.mapper.range.high",
        label="Upper",
        springy=True,
        editor=TextEditor(enter_set=True, auto_set=False),
    ),
    Item(
        "object.mapper.range.low",
        label="Lower",
        springy=True,
        editor=TextEditor(enter_set=True, auto_set=False),
    ),
    show_border=True,
    label="Limits",
)
tick_grp = VGroup(
    Item("tick_color", label="Color"),
    # editor=EnableRGBAColorEditor()),
    Item("tick_weight", label="Thickness"),
    # Item('tick_label_font', label='Font'),
    Item("tick_label_color", label="Label color"),
    # editor=EnableRGBAColorEditor()),
    HGroup(Item("tick_in", label="Tick in"), Item("tick_out", label="Tick out")),
    Item("tick_visible", label="Visible"),
    # Item("tick_interval", label="Interval", editor=TextEditor(evaluate=float_or_auto)),
    # Item(
    #     "wrapper.tick_label_format_str",
    #     tooltip="Enter a formatting string to apply to the tick labels. Currently the only supported "
    #     "option is to enter a number from 0-9 specifying the number of decimal places",
    #     label="Format",
    # ),
    show_border=True,
    label="Ticks",
)
line_grp = VGroup(
    Item("axis_line_color", label="Color"),
    # editor=EnableRGBAColorEditor()),
    Item("axis_line_weight", label="Thickness"),
    Item("axis_line_visible", label="Visible"),
    show_border=True,
    label="Line",
)
title_grp = VGroup(
    Item("title", label="Title", editor=TextEditor()),
    Item("title_font", label="Font"),
    Item("title_color", label="Color"),
    show_border=True,
    label="Title",
)
AxisView = View(VGroup(limit_grp,
                       title_grp,
                       tick_grp,
                       line_grp),
                title="Edit Axis",
                buttons=['OK', ])


class AxisViewHandler(Handler):
    def init(self, info):
        from pyface.qt import QtCore
        info.ui.control.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

# ============= EOF =============================================
