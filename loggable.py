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
import logging

from traits.api import HasTraits, Str, Dict

shandler = logging.StreamHandler()


class Loggable(HasTraits):
    logger_name = Str
    name = Str
    logger = None
    configobj = Dict

    def __init__(self, cfg=None, *args, **kw):
        if cfg is None:
            cfg = {}

        name = cfg.get('name', self.__class__.__name__)
        super().__init__(name=name, *args, **kw)

        if self.logger_name:
            name = self.logger_name
        elif self.name:
            name = self.name
        else:
            name = self.__class__.__name__

        if self.logger is None:
            name = f"{name:<30}"
            l = logging.getLogger(name)
            l.setLevel(logging.DEBUG)
            l.addHandler(shandler)
            self.logger = l

        self.configobj = cfg

    def info(self, msg):
        self.logger.info(msg)

    def debug(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def debug_exception(self):
        import traceback

        exc = traceback.format_exc()
        self.debug(exc)
        return exc
# ============= EOF =============================================
