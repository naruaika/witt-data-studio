# move_node.py
#
# Copyright (c) 2025 Naufan Rusyda Faikar <hello@naruaika.me>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# 	http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

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