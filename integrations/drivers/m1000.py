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
from integrations.drivers.base import BaseADCDriver
from traits.api import Str


SHORT_FORM_PROMPT = "$"
LONG_FORM_PROMPT = "#"


class M1000(BaseADCDriver):
    """ """
    address = Str

    # short_form_prompt = "$"
    # long_form_prompt = "#"
    # voltage_scalar = 1
    # units = ""

    # def load_additional_args(self, config):
    #     """ """
    #     self.set_attribute(config, "address", "General", "address")
    #     self.set_attribute(
    #         config, "voltage_scalar", "General", "voltage_scalar", cast="float"
    #     )
    #     self.set_attribute(config, "units", "General", "units")
    #     if self.address is not None:
    #         return True

    # def read_device(self, **kw):
    #     """ """
    #     res = super(M1000, self).read_device(**kw)
    #     if res is None:
    #         cmd = "RD"
    #         addr = self.address
    #         cmd = "".join((self.short_form_prompt, addr, cmd))
    #
    #         res = self.ask(cmd, **kw)
    #         res = self._parse_response_(res)
    #         # if res is not None:
    #         #     res = Q_(res, self.units)
    #
    #     return res
    def load(self, cfg):
        self.address = cfg.get('address', '')

    def _read_channel(self, channel):
        cmd = "RD"
        addr = self.address
        cmd = "".join((SHORT_FORM_PROMPT, addr, cmd))

        res = self.ask(cmd)
        return self._parse_response(res)

    def _parse_response(self, r, form="$", kind=None):
        """
        typical response form
        short *+00072.00
        long *1RD+00072.00A4
        """
        # func = (
        #     lambda X: float(X[5:-2]) if form == self.long_form_prompt else float(X[2:])
        # )

        if form == LONG_FORM_PROMPT:
            def func(rr):
                return float(rr[5:-2])
        else:
            def func(rr):
                return float(rr[2:])

        if r:
            if kind == "block":
                r = r.split(",")
                return [func(ri) for ri in r if ri is not ""]
            else:
                return func(r)
# ============= EOF =============================================
