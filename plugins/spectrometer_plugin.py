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

from figure import Figure
from hardware import SpectrometerController
from persister import JSONPersister
from plugin import BasePlugin
from traits.api import List, Instance


class SpectrometerPlugin(BasePlugin):
    id = 'laba.plugin.spectrometer'
    automation_commands = List(contributes_to='laba.automation.commands')
    controller = Instance(SpectrometerController)

    def _automation_commands_default(self):
        return [('measure', self._measure), ]

    def _measure(self, ncycles=1, hops=None):
        """

        :param ncycles: use ncycles=1 for multi-collection
        :return:
        """
        self.debug('measure')
        # open a window for displaying our measurement graph
        figure = self._setup_figure()
        figure.edit_traits()

        # setup persistence
        with JSONPersister() as persister:
            # do measurement
            for cycle in range(ncycles):
                # do cycle
                self.debug(f'going cycle = {cycle}')
                for i, hop in enumerate(hops):
                    # do hop
                    self.debug(f'{i}, hop={hop}')

                    self.set_ionbeam_position(hop)
                    period = hop['period']
                    for c in range(hop['counts']):
                        st = time.time()
                        self.record_counts(hop, persister)

                        # delay between counts
                        et = time.time() - st
                        p = period - et
                        if p > 0:
                            time.sleep(p)

    def record_counts(self, hop, persister):
        self.debug(f"record counts for {hop['detectors']}")
        intensities = self.controller.get_intensities(hop['detectors'])
        payload = {'time': time.time(), 'intensities': intensities}
        persister.add('intensities', payload)

    def set_ionbeam_position(self, hop):
        self.debug(f"position {hop['iso']} on det={hop['det']}")
        self.controller.set_ionbeam_position(hop['iso'], hop['det'])

    def _setup_figure(self):
        figure = Figure()
        return figure
# ============= EOF =============================================
