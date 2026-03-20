# select_by_rubberband.py
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

from .... import environment as env

from ....core.action import Action

from ..editor import NodeEditor

class ActionSelectByRubberband(Action):

    def __init__(self,
                 editor: NodeEditor,
                 combo:  bool = False,
                 ) ->    None:
        """"""
        window = env.APP.get_active_main_window()
        owner = window.node_editor

        super().__init__(owner)

        self.editor = editor
        self.combo  = combo

        self.old_rubber_band    = None
        self.old_selected_nodes = []

    def do(self,
           undoable: bool = True,
           ) ->      bool:
        """"""
        self.old_selected_nodes = copy(self.editor.selected_nodes)

        if not self.combo:
            while self.editor.selected_nodes:
                node = self.editor.selected_nodes[0]
                node.unselect()

        if self.old_rubber_band:
            self.editor.rubber_band = copy(self.old_rubber_band)
        else:
            self.old_rubber_band = copy(self.editor.rubber_band)

        p1, p2 = self.editor.rubber_band
        x1, y1 = p1
        x2, y2 = p2

        sel_x      = min(x1, x2)
        sel_y      = min(y1, y2)
        sel_width  = abs(x1 - x2)
        sel_height = abs(y1 - y2)

        sel_right  = sel_x + sel_width
        sel_bottom = sel_y + sel_height

        for node in self.editor.nodes:
            allocation = node.get_allocation()

            node_x      = allocation.x
            node_y      = allocation.y
            node_width  = allocation.width
            node_height = allocation.height

            node_right  = node_x + node_width
            node_bottom = node_y + node_height

            if (
                sel_x      < node_right  and
                sel_right  > node_x      and
                sel_y      < node_bottom and
                sel_bottom > node_y
            ):
                node.toggle()

        self.editor.rubber_band = None

        return True

    def undo(self) -> bool:
        """"""
        while self.editor.selected_nodes:
            node = self.editor.selected_nodes[0]
            node.unselect()

        for node in self.old_selected_nodes:
            node.select()

        return True

    def isduplicate(self,
                    action: Action,
                    ) ->    bool:
        """"""
        return False # TODO