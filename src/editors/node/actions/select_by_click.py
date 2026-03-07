# select_by_click.py
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

class ActionSelectByClick(Action):

    def __init__(self,
                 editor: NodeEditor,
                 node:   NodeFrame = None,
                 combo:  bool      = False,
                 ) ->    None:
        """"""
        window = env.app.get_active_main_window()
        owner = window.node_editor

        super().__init__(owner)

        self.editor = editor
        self.node   = node
        self.combo  = combo

    def do(self,
           undoable: bool = True,
           ) ->      bool:
        """"""
        self.old_selected_nodes = copy(self.editor.selected_nodes)

        if self.combo:
            if self.node:
                self.node.toggle()

        else:
            while self.editor.selected_nodes:
                node = self.editor.selected_nodes[0]
                node.unselect()

            if self.node:
                self.node.select()

        window = self.editor.get_root()
        window.StatusBar.populate()

        return True

    def undo(self) -> bool:
        """"""
        while self.editor.selected_nodes:
            node = self.editor.selected_nodes[0]
            node.unselect()

        for node in self.old_selected_nodes:
            node.select()

        window = self.editor.get_root()
        window.StatusBar.populate()

        return True

    def isduplicate(self,
                    action: Action,
                    ) ->    bool:
        """"""
        if self.combo:
            return False

        if self.editor.selected_nodes == [self.node]:
            return True

        return False