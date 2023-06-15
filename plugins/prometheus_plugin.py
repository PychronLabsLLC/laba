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
from plugin import BasePlugin
from traits.api import List
from prometheus_client import start_http_server, Gauge


class PrometheusPlugin(BasePlugin):
    device_events = List(contributes_to="laba.device.events")

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        g = Gauge("pressure", "MKS description")

        def mks_func(obj, old, name, new):
            self.debug(f"handling mks update {new}")
            if "pressure" in new:
                g.set(new["value"])

        self.device_events = [
            ("mks", mks_func, "update"),
        ]

    def start(self):
        start_http_server(self.config("port", 8000))

    # def _device_events_default(self):
    #     return [('mks', self._handle_update, 'update'), ]

    # ============= EOF =============================================
