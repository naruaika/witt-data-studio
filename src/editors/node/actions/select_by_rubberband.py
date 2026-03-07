# select_by_rubberband.py
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

from .... import environment as env
from ....core.action import Action

from ..editor import NodeEditor
from ..frame import NodeFrame

class ActionSelectByRubberband(Action):

    def __init__(self,
                 editor: NodeEditor,
                 combo:  bool = False,
                 ) ->    None:
        """"""
        window = env.app.get_active_main_window()
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