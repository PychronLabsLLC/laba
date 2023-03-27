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

import yaml
from envisage.extension_point import ExtensionPoint
from envisage.ids import TASK_EXTENSIONS
from envisage.plugin import Plugin
from envisage.ui.tasks.task_extension import TaskExtension
from envisage.ui.tasks.task_factory import TaskFactory
from pyface.action.schema.schema import SMenu, SMenuBar
from pyface.action.schema.schema_addition import SchemaAddition
from traitsui.menu import Action

from automation import Automation
from dashboard import Dashboard, HistoryDashboard
from figure import Figure
from hardware.device import Device
from loggable import Loggable
from traits.api import List, Instance

from paths import paths
from persister import JSONPersister
from task import HardwareTask, SequencerTask
from util import yload


class BasePlugin(Plugin, Loggable):
    service_offers = List(contributes_to="envisage.service_offers")
    preferences = List(contributes_to="envisage.preferences")
    preferences_panes = List(contributes_to="envisage.ui.tasks.preferences_panes")
    tasks = List(contributes_to="envisage.ui.tasks.tasks")


class HardwarePlugin(BasePlugin):
    # an extension point for adding additional commands to automations
    automation_commands = ExtensionPoint(List, id='laba.automation.commands')

    def _hardware_task_factory(self):
        devices = self.application.get_services(Device)

        # ds = [HistoryDashboard(self.application)]
        ds = []

        yobj = yload(paths.dashboards_path)
        # with open(paths.dashboards_path, 'r') as rfile:
        #     yobj = yaml.load(rfile, yaml.SafeLoader)
        for d in yobj:
            ds.append(Dashboard(self.application, d))
        ds.append(HistoryDashboard(self.application))
        # automations = []
        # with open(paths.automations_path, 'r') as rfile:
        #     yobj = yaml.load(rfile, yaml.SafeLoader)

        # yobj = yload(paths.automations_path)
        # for automation in yobj:
        #     automations.append(Automation(automation))
        automations = [Automation(a) for a in yload(paths.automations_path)]

        return HardwareTask(devices=devices, dashboards=ds, automations=automations,
                            selection=ds[0])

    def _sequence_task_factory(self):
        return SequencerTask(application=self.application)

    def _tasks_default(self):
        return [

            TaskFactory(
                id='laba.sequencer.task',
                name='Sequencer',
                factory=self._sequence_task_factory,
            ),
            TaskFactory(
                id="laba.hardware.task",
                name="Hardware",
                factory=self._hardware_task_factory,
                # image="repo",
            ),

        ]


class SwitchPlugin(BasePlugin):
    automation_commands = List(contributes_to='laba.automation.commands')

    def _automation_commands_default(self):
        return [('open_switch', self.open_switch),
                ('close_switch', self.close_switch)]

    def open_switch(self, name, *args, **kw):
        self._actuate_switch(name, True, *args, **kw)

    def close_switch(self, name, *args, **kw):
        self._actuate_switch(name, False, *args, **kw)

    def _actuate_switch(self, name, state, *args, **kw):
        for sw in self.application.get_services(Device):
            if not hasattr(sw, 'switches'):
                continue

            for si in sw.switches:
                if si.name == name:
                    func = sw.open_switch if state else sw.close_switch
                    func(name, *args, **kw)
                    break


class BaseSpectrometerController(Device):
    def set_ionbeam_position(self, iso, detector):
        raise NotImplementedError

    def get_intensities(self, detectors):
        raise NotImplementedError


class SpectrometerPlugin(BasePlugin):
    automation_commands = List(contributes_to='laba.automation.commans')
    controller = Instance(BaseSpectrometerController)

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
