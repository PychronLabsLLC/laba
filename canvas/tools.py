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
from enable.base_tool import BaseTool


class CanvasInteractor(BaseTool):
    def normal_mouse_move(self, event):
        if self.hittest(event):
            event.window.set_pointer("hand")
        else:
            event.window.set_pointer("arrow")

    def hittest(self, event):
        for o in self.component.overlays:
            if o.hittest(event.x, event.y):
                return o

    def normal_left_down(self, event):
        if o := self.hittest(event):
            state = self.controller.toggle_switch(o.name)
            o.state = state
            self.component.request_redraw()


# ============= EOF =============================================
