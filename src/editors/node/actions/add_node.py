# add_node.py
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

from copy          import copy
from gi.repository import GLib

from .... import environment as env

from ....core.action import Action

from ..editor import NodeEditor
from ..frame  import NodeFrame

class ActionAddNode(Action):

    def __init__(self,
                 editor: NodeEditor,
                 nodes:  list[NodeFrame],
                 ) ->    None:
        """"""
        window = env.APP.get_active_main_window()
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
        window = env.APP.get_active_main_window()
        freezing = window.history.freezing
        window.history.freezing = True

        ActionDeleteNode(self.editor, self.nodes).do()

        window.history.freezing = freezing

        return True

from .delete_node import *