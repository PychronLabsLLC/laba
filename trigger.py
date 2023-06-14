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



class Trigger(Loggable):
    def handle(self, obj, name, old, new):
        self.debug(f'handle {obj}, {new}')
        for test in self.config('tests'):
            if self._test(obj, test, new):
                self._action(obj, test, new)
                break

    def _test(self, obj, test, new):
        if test['attribute'] in new:
            attribute = test['attribute']
            tvalue = new[attribute]
            from_value, to_value = None, None

            for k, v in test.items():
                ret = False
                if k == 'attribute':
                    continue

                try:
                    v = float(v)
                except (ValueError, TypeError):
                    continue

                if k == 'le':
                    ret = tvalue <= v
                elif k == 'ge':
                    ret = tvalue >= v
                elif k == 'lt':
                    ret = tvalue < v
                elif k == 'gt':
                    ret = tvalue > v
                elif k == 'eq':
                    ret = tvalue == v
                elif k == 'from':
                    from_value = v
                elif k == 'to':
                    to_value = v

                if k not in ('from', 'to'):
                    self.debug(f'testing {tvalue} {k} {v}')

                if to_value is not None and from_value is not None:
                    self.debug(f'testing {tvalue} {from_value} <= {tvalue} <= {to_value}')
                    ret = from_value <= tvalue <= to_value

                if ret:
                    return True

    def _action(self, obj, test, new):
        self.info(f'Trigger fired, {self}')
        action = self.config('action')
        for k, v in action.items():
            if k == 'log':
                self.info(f'trigger log: {v}')

# ============= EOF =============================================
