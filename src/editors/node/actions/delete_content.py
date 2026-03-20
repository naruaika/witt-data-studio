# delete_content.py
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

from .... import environment as env

from ....core.action import Action

from ..content import NodeContent
from ..editor  import NodeEditor
from ..frame   import NodeFrame

class ActionDeleteContent(Action):

    def __init__(self,
                 editor:  NodeEditor,
                 content: NodeContent,
                 node:    NodeFrame = None,
                 cindex:  int       = None,
                 ) ->     None:
        """"""
        window = env.APP.get_active_main_window()
        owner = window.node_editor

        super().__init__(owner)

        node = node or content.Frame

        if cindex is None:
            try:
                cindex = node.contents.index(content)
            except:
                cindex = -1

        self.editor  = editor
        self.content = content
        self.node    = node
        self.cindex  = cindex

    def do(self,
           undoable: bool = True,
           ) ->      bool:
        """"""
        if self.cindex == -1:
            return False

        self.content.do_remove(self.content)
        return True

    def undo(self) -> bool:
        """"""
        self.node.contents.insert(self.cindex, self.content)

        sibling = self.node.Body.get_first_child()
        child = self.content.Container

        if not sibling or self.cindex == 0:
            self.node.Body.prepend(child)
        else:
            index = 1
            while sibling:
                if index == self.cindex:
                    self.node.Body.insert_child_after(child, sibling)
                    break
                sibling = sibling.get_next_sibling()
                index += 1

        return True