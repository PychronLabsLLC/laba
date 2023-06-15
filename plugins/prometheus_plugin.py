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

        events = []
        print(self.configobj)
        for gconfig in self.config("gauges", []):
            g = Gauge(gconfig["name"], gconfig.get("description", ""))
            self.debug(f"adding gauge {gconfig['name']}")

            def func(obj, old, name, new):
                if 'value' in new:
                    self.debug(f"updating gauge {gconfig['name']} to {new['value']}")
                    g.set(new['value'])

            event = (gconfig["name"], func, gconfig.get('event', 'update'))
            events.append(event)

        self.device_events = events

    def start(self):
        start_http_server(self.config("port", 8000))

    # def _device_events_default(self):
    #     return [('mks', self._handle_update, 'update'), ]

    # ============= EOF =============================================
