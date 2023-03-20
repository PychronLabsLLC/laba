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
import itertools

from numpy import polyval

from hardware.device import Device
from hardware.util import get_float
from traits.api import HasTraits, Str, List

# class ADC(Device):
#     @get_float()
#     def read_channel(self, channel):
#         self.debug(f'read channel {channel}')
#         self.driver.read_channel(channel)

counter = itertools.count()


class Channel(HasTraits):
    name = Str
    address = Str
    mapping = List

    def __init__(self, *args, **kw):
        if kw['mapping']:
            mapping = kw.pop('mapping')
            self.mapping = [float(c) for c in mapping.split(',')]

        super().__init__(*args, **kw)

    def map_value(self, v):
        """
        return v(olts) converted to channel units

        :param v:
        :return:
        """
        if v is None:
            v = next(counter)

        if self.mapping:
            v = polyval(self.mapping, v)
        return v


class ADC(Device):
    channels = List(Channel)

    def load(self, cfg):
        self.channels = [Channel(**ci) for ci in cfg['channels']]

    def get_value(self, idx=0, datastream='default'):
        ch = self.channels[idx]
        v = self.driver.read_channel(ch.address)
        vv = ch.map_value(v)
        self.debug(f'get value volts={v}, value={vv}')

        self.update = {'datastream': datastream,
                       'value': vv}
        return vv
# ============= EOF =============================================
