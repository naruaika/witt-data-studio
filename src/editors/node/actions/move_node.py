# move_node.py
#
# Copyright (c) 2025 Naufan Rusyda Faikar <hello@naruaika.me>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from copy import copy
import gc

from .... import environment as env
from ....core.action import Action

from ..editor import NodeEditor
from ..frame import NodeFrame

class ActionMoveNode(Action):

    def __init__(self,
                 editor:    NodeEditor,
                 nodes:     list[NodeFrame],
                 positions: list[tuple],
                 ) ->       None:
        """"""
        window = env.app.get_active_main_window()
        owner = window.node_editor

        super().__init__(owner)

        self.editor    = editor
        self.nodes     = copy(nodes)
        self.positions = positions

    def do(self,
           undoable: bool = True,
           ) ->      bool:
        """"""
        if not self.nodes:
            return False

        canvas = self.editor.Canvas

        canvas_width  = canvas.get_width()
        canvas_height = canvas.get_height()

        for index, node in enumerate(self.nodes):
            node_width  = node.get_width()  or 175
            node_height = node.get_height() or 125
            max_x = canvas_width  - node_width
            max_y = canvas_height - node_height

            node.x = self.positions[index][1][0]
            node.y = self.positions[index][1][1]
            node.x = int(min(max(0, node.x), max_x))
            node.y = int(min(max(0, node.y), max_y))

            canvas.move(node, node.x, node.y)
            node.compute_points()

        self.editor.collect_points()

        gc.collect()

        return True

    def undo(self) -> bool:
        """"""
        window = env.app.get_active_main_window()
        freezing = window.history.freezing
        window.history.freezing = True

        positions = []
        for position in self.positions:
            positions.append((position[1], position[0]))

        action = ActionMoveNode(self.editor,
                                self.nodes,
                                positions)
        action.do()

        window.history.freezing = freezing

        return True