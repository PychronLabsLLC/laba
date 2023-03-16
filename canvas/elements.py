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


# ============= EOF =============================================
class CanvasOverlay(AbstractOverlay):
    def hittest(self, x, y):
        return
    # def overlay(self, component, gc, view_bounds, mode):
    #     with gc:
    #         gc.rect(0, 0, 50, 50)
    #         gc.stroke_path()


class CanvasElement(AbstractOverlay):
    def hittest(self, x, y):
        return self.x < x < self.x + self.width and self.y < y <self.y + self.height


class CanvasSwitch(CanvasElement):
    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
        with gc:
            print('asdf', self.x, self.y)
            gc.translate_ctm(self.x, self.y)
            gc.rect(0, 0, self.width, self.height)
            gc.stroke_path()

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
