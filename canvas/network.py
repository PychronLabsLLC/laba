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
from traits.api import List, HasTraits, Str, Bool

from canvas.elements import CanvasElement, CanvasConnection, CanvasSwitch
from loggable import Loggable


class Node(HasTraits):
    name = Str
    children = List
    state = Str
    edges = List

    def set_color(self, c):
        if isinstance(self.element, CanvasSwitch):
            if self.element.state == 'open':
                self.element.active_color = c
                for ci in self.children:
                    ci.set_color(c)

                for ei in self.edges:
                    ei.active_color = c
        else:
            self.element.active_color = c
            for ci in self.children:
                ci.set_color(c)

            for ei in self.edges:
                ei.active_color = c


def max_precedence(tree):
    mp, color = tree.element.precedence, tree.element.default_color
    if tree.children:
        for ci in tree.children:
            if isinstance(ci.element, CanvasSwitch):
                if ci.state != 'open':
                    continue
            mpi, ci = max_precedence(ci)
            if mpi > mp:
                mp = mpi
                color = ci

    return mp, color


def split_tree(pivot):
    try:
        left = pivot.children[0]
    except IndexError:
        left = None

    try:
        right = pivot.children[1]
    except IndexError:
        right = None

    return left, right


class CanvasNetwork(Loggable):
    nodes = List

    def __init__(self, dv, *args, **kw):
        super().__init__(*args, **kw)
        self.dv = dv

    def _build_tree(self, name):
        def make_node(elem, visited=set()):
            if not isinstance(elem, CanvasElement):
                elem = next((o for o in self.dv.overlays
                             if isinstance(o, CanvasElement) and o.name == elem))

            if elem in visited:
                return

            visited.add(elem)

            cs = []
            es = []
            for o in self.dv.underlays:
                if isinstance(o, CanvasConnection):
                    if o.start == elem:
                        if nn := make_node(o.end, visited):
                            cs.append(nn)
                        es.append(o)
                    elif o.end == elem:
                        if nn := make_node(o.start, visited):
                            cs.append(nn)
                        es.append(o)

            n = Node(name=elem.name,
                     state=elem.state,
                     element=elem,
                     children=cs,
                     edges=es)
            return n

        tree = make_node(name)
        return tree

    def update(self, name):
        tree = self._build_tree(name)

        if tree.state == 'closed':
            # split the network into two subnetworks
            # split until only 2 elements
            # get the max precedence of those two elements
            # tree.set_color(tree.element.default_color)
            for e in tree.edges:
                e.active_color = e.default_color

            left, right = split_tree(tree)
            if left:
                leftp = max_precedence(left)
                left.set_color(leftp[1])
            if right:
                rightp = max_precedence(right)
                right.set_color(rightp[1])
        else:
            # get max precedence of this tree
            maxp, color = max_precedence(tree)
            tree.set_color(color)

# ============= EOF =============================================
