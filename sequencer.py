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
from loggable import Loggable
from traits.api import List, File

from util import yload


class SequenceError(BaseException):
    pass


class AutomationError(BaseException):
    pass


class SequenceStep(Loggable):
    automations = List

    def run(self):
        ts = []
        for a in self.automations:
            try:
                t = a.run(block=False)
                ts.append(t)
            except AutomationError as err:
                self.warning(f'Automation {a} error: {err}')
                break

        for ti in ts:
            ti.join()


class Sequence(Loggable):
    steps = List

    def run(self):
        self.debug('run sequence')
        for i, si in enumerate(self.steps):
            self.debug(f'do step {i}')
            si.run()


class Sequencer(Loggable):
    sequences = List(Sequence)
    path = File

    def load(self):
        self.sequences = yload(self.path)

    def save(self):
        pass

    def run(self):
        self.debug('run sequences')
        for s in self.sequences:
            try:
                s.run()
            except SequenceError as err:
                self.warning(f'Sequence {s} error: {err}')

# ============= EOF =============================================
