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
import yaml
from pyface.image_resource import ImageResource
from traitsui.editors import ButtonEditor
from traitsui.item import Item, UItem


def icon(name):
    name = f'{name}.png'
    icon_search_path = './resources/icons'
    return ImageResource(name=name, search_path=icon_search_path)


class MUItem(UItem):
    def get_label(self, ui):
        return ""


def icon_button_editor(name, image, editor_kw=None, **kw):
    if editor_kw is None:
        editor_kw = {}

    image = icon(image)

    return MUItem(
        name, style="custom", editor=ButtonEditor(image=image, **editor_kw),
        **kw
    )


def import_klass(k):
    args = k.split(".")
    pkg, klass = ".".join(args[:-1]), args[-1]
    mod = __import__(pkg, fromlist=[klass])

    return getattr(mod, klass)


def yload(path):
    with open(path, 'r') as rfile:
        return yaml.load(rfile, yaml.SafeLoader)

# ============= EOF =============================================
