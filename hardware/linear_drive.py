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
from hardware.device import Device
from traits.api import Float, HasTraits, Instance


class LinearMapper(HasTraits):
    min_data = Float(0)
    max_data = Float(1)
    min_raw = Float(0)
    max_raw = Float(100)

    def map_raw(self, data):
        """
        map the data value to a raw value
        :param raw:
        :return:
        """
        return self._map(data, self.min_raw, self.max_raw, self.min_data, self.max_data)

    def map_data(self, raw):
        """
        map the raw value to a data value
        :param data:
        :return:
        """
        return self._map(raw, self.min_data, self.max_data, self.min_raw, self.max_raw)

    def _map(self, x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


class LinearDrive(Device):
    mapper = Instance(LinearMapper, ())

    def move_to(self, position, **kw):
        """
        move to position
        :param position:
        :return:
        """
        raw = self.mapper.map_raw(position)
        self._move_to(raw, **kw)

    def _move_to(self, raw, **kw):
        self.driver.move_absolute(raw, **kw)

# ============= EOF =============================================
