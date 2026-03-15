# edit_node.py
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

from gi.repository import GLib

from .... import environment as env
from ....core.action import Action

from ..editor import NodeEditor
from ..frame import NodeFrame

class ActionEditNode(Action):

    def __init__(self,
                 editor: NodeEditor,
                 node:   NodeFrame,
                 values: tuple,
                 ) ->    None:
        """"""
        window = env.app.get_active_main_window()
        owner = window.node_editor

        super().__init__(owner)

        self.editor = editor
        self.node   = node
        self.values = values

    def do(self,
           undoable: bool = True,
           ) ->      bool:
        """"""
        self.node.do_restore(self.values[1])

        GLib.timeout_add(50, self.editor.do_collect_points, [self.node])

        return True

    def undo(self) -> bool:
        """"""
        window = env.app.get_active_main_window()
        freezing = window.history.freezing
        window.history.freezing = True

        values = (self.values[1], self.values[0])
        ActionEditNode(self.editor, self.node, values).do()

        window.history.freezing = freezing

        return True