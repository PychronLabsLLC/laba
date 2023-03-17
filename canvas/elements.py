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
from enable.abstract_overlay import AbstractOverlay
from kiva.fonttools import str_to_font
from traits.api import Str, Bool, Enum, Float


# ============= EOF =============================================
class CanvasOverlay(AbstractOverlay):
    def hittest(self, x, y):
        return
    # def overlay(self, component, gc, view_bounds, mode):
    #     with gc:
    #         gc.rect(0, 0, 50, 50)
    #         gc.stroke_path()


class CanvasElement(AbstractOverlay):
    name = Str
    font = 'arial 14'

    def hittest(self, x, y):
        (sx, sy), sw, sh = self._map_screen()
        return sx < x < sx + sw and sy < y < sy + sh

    def _map_screen(self):
        (x, y), (zx, zy), (wx, wy) = self.component.map_screen([(self.x, self.y),
                                                                (0, 0),
                                                                (self.width, self.height)])
        return (x, y), wx - zx, zy - wy

    def _render_name(self, gc, x, y, w, h):
        if self.name:
            with gc:
                gc.set_font(str_to_font(self.font))
                # c = self.text_color if self.text_color else self.default_color
                # gc.set_fill_color(self._convert_color(self.name_color))
                txt = str(self.name)
                self._render_textbox(gc, x, y, w, h, txt)

    def _render_textbox(self, gc, x, y, w, h, txt):
        tw, th, _, _ = gc.get_full_text_extent(txt)
        x = x + w / 2.0 - tw / 2.0
        y = y + h / 2.0 - th / 2.0

        self._render_text(gc, txt, x, y)

    def _render_text(self, gc, t, x, y):
        with gc:
            gc.translate_ctm(x, y)
            gc.set_fill_color((0, 0, 0))
            gc.set_text_position(0, 0)
            gc.show_text(t)


def rounded_rect(gc, x, y, width, height, corner_radius):
    with gc:
        gc.translate_ctm(x, y)  # draw a rounded rectangle
        x = y = 0
        gc.begin_path()

        hw = width * 0.5
        hh = height * 0.5
        if hw < corner_radius:
            corner_radius = hw * 0.5
        elif hh < corner_radius:
            corner_radius = hh * 0.5

        gc.move_to(x + corner_radius, y)
        gc.arc_to(x + width, y, x + width, y + corner_radius, corner_radius)
        gc.arc_to(
            x + width, y + height, x + width - corner_radius, y + height, corner_radius
        )
        gc.arc_to(x, y + height, x, y, corner_radius)
        gc.arc_to(x, y, x + width + corner_radius, y, corner_radius)
        gc.draw_path()


class CanvasSwitch(CanvasElement):
    corner_radius = 10
    state = Enum('unknown', 'open', 'closed', 'moving')
    voltage = Float

    def hittest(self, x, y):
        (sx, sy), sw, sh = self._map_screen()
        return sx < x < sx + sw and sy < y < sy + sw

    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
        color = (0.5, 0.5, 0.5)
        if self.state == 'open':
            color = (0, 1, 0)
        elif self.state == 'closed':
            color = (1, 0, 0)
        elif self.state == 'moving':
            color = (1, 1, 0)

        (x, y), w, h = self._map_screen()
        with gc:
            scale = 0.5
            mcolor = [c * scale for c in color]
            gc.set_line_width(10)
            gc.set_stroke_color(mcolor)
            gc.set_fill_color(color)
            rounded_rect(gc, x, y, w, w, self.corner_radius)

            self._render_name(gc, x, y, w, w)
            # voltage
            with gc:
                gc.translate_ctm(0, -10)
                gc.set_font(str_to_font(self.font))
                # c = self.text_color if self.text_color else self.default_color
                # gc.set_fill_color(self._convert_color(self.name_color))
                txt = f'{self.voltage:0.3f}'
                self._render_textbox(gc, x, y, w, h, txt)

# class SwitchOverlay(AbstractOverlay):
#     def __init__(self, *args, **kw):
#         super().__init__(*args, **kw)
#         self.switches = [CanvasSwitch(component=self,
#                                       x=10, y=20, width=25, height=25)]
#         self.overlays = self.switches
#
#     def overlay(self, component, gc, view_bounds, mode):
#         for o in self.overlays:
#             o.overlay(component, gc, view_bounds, mode)
