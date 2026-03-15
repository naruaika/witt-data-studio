# select_by_click.py
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