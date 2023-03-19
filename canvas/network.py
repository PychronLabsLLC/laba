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


class CanvasNetwork(Loggable):
    nodes = List

    def __init__(self, dv, *args, **kw):
        super().__init__(*args, **kw)
        self.dv = dv

    def _build_tree(self, name):
        def make_node(node):
            if not isinstance(node, CanvasElement):
                node = next((o for o in self.dv.overlays
                             if isinstance(o, CanvasElement) and o.name == node))

            if node.visited:
                return

            node.visited = True
            cs = []
            es = []
            for o in self.dv.underlays:
                if isinstance(o, CanvasConnection):
                    if o.start == node:
                        if nn := make_node(o.end):
                            cs.append(nn)
                        es.append(o)
                    elif o.end == node:
                        if nn := make_node(o.start):
                            cs.append(nn)
                        es.append(o)

            n = Node(name=node.name,
                     state=node.state,
                     element=node,
                     children=cs,
                     edges=es)
            return n

        for ov in self.dv.overlays:
            if isinstance(ov, CanvasElement):
                ov.visited = False

        tree = make_node(name)
        return tree

    def update(self, name):
        tree = self._build_tree(name)

        if tree.state == 'closed':
            # split the network into two subnetworks
            # split until only 2 elements
            # get the max precedence of those two elements
            left, right = self._split_tree(tree)

            if left:
                leftp = self._max_precedence(left)
                left.set_color(leftp[1])
            if right:
                rightp = self._max_precedence(right)
                right.set_color(rightp[1])
        else:
            # get max precedence of this network
            maxp, color = self._max_precedence(tree)
            tree.set_color(color)

    def _split_tree(self, pivot):
        try:
            left = pivot.children[0]
        except IndexError:
            left = None

        try:
            right = pivot.children[1]
        except IndexError:
            right = None

        return left, right

    def _max_precedence(self, tree):
        mp, color = tree.element.precedence, tree.element.default_color
        if tree.children:
            for ci in tree.children:
                if isinstance(ci.element, CanvasSwitch):
                    if ci.state != 'open':
                        continue

                mpi, ci = self._max_precedence(ci)
                if mpi > mp:
                    mp = mpi
                    color = ci

        return mp, color

    # def update(self, node):
    #     if isinstance(node, str):
    #         for o in self.dv.overlays:
    #             if isinstance(o, CanvasElement):
    #                 o.visited = False
    #
    #         node = next((o for o in self.dv.overlays if o.name == node))
    #
    #     if node.visited:
    #         return node.precedence, node
    #
    #     node.visited = True
    #     name = node.name
    #     connections = [o for o in self.dv.underlays
    #                    if isinstance(o, CanvasConnection) and (o.start.name == name or o.end.name == name)]
    #     if isinstance(node, CanvasSwitch):
    #         ap, an = 0, None
    #         bp, bn = 0, None
    #
    #         # traverse network
    #         try:
    #             a = self.traverse(node, connections[0])
    #             if a:
    #                 ap, an = a
    #         except IndexError:
    #             pass
    #
    #         try:
    #             b = self.traverse(node, connections[1])
    #             if b:
    #                 bp, bn = b
    #         except IndexError:
    #             pass
    #
    #         print(node.name, node.state, ap, bp)
    #         if node.state == 'open':
    #             c = None
    #             if ap > bp:
    #                 c = an.default_color
    #                 an.active_color = an.default_color
    #             else:
    #                 if bn:
    #                     c = bn.default_color
    #                     bn.active_color = bn.default_color
    #             if c:
    #                 node.active_color = c
    #                 for ci in connections:
    #                     ci.active_color = c
    #         else:
    #             # for ci in connections:
    #             #     ci.active_color = ci.default_color
    #
    #             if an:
    #                 if isinstance(an, CanvasSwitch):
    #                     if an.state == 'closed':
    #                         connections[0].active_color = connections[0].default_color
    #                 else:
    #                     connections[0].active_color = an.active_color
    #
    #         return 0, node
    #     else:
    #         for ci in connections:
    #             ci.active_color = node.default_color
    #
    #         return node.precedence, node
    #
    # def traverse(self, node, edge):
    #     if edge.start == node:
    #         return self.update(edge.end)
    #     elif edge.end == node:
    #         return self.update(edge.start)

# ============= EOF =============================================
