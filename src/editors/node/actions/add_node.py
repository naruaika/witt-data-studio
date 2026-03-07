# add_node.py
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
from gi.repository import GLib

from .... import environment as env
from ....core.action import Action

from ..editor import NodeEditor
from ..frame import NodeFrame

class ActionAddNode(Action):

    def __init__(self,
                 editor: NodeEditor,
                 nodes:  list[NodeFrame],
                 ) ->    None:
        """"""
        window = env.app.get_active_main_window()
        owner = window.node_editor

        super().__init__(owner)

        self.editor = editor
        self.nodes  = copy(nodes)

    def do(self,
           undoable: bool = True,
           ) ->      bool:
        """"""
        if not self.nodes:
            return False

        for node in self.nodes:
            self.editor.Canvas.put(node, node.x, node.y)
            self.editor.nodes.append(node)

            if node.is_selected:
                self.editor.selected_nodes.append(node)

        GLib.timeout_add(50, self.editor.do_collect_points, self.nodes)

        return True

    def undo(self) -> bool:
        """"""
        window = env.app.get_active_main_window()
        freezing = window.history.freezing
        window.history.freezing = True

        ActionDeleteNode(self.editor, self.nodes).do()

        window.history.freezing = freezing

        return True

from .delete_node import *