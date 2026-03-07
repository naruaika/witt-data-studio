# delete_content.py
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

from .... import environment as env
from ....core.action import Action

from ..content import NodeContent
from ..editor import NodeEditor
from ..frame import NodeFrame

class ActionDeleteContent(Action):

    def __init__(self,
                 editor:  NodeEditor,
                 content: NodeContent,
                 node:    NodeFrame = None,
                 cindex:  int       = None,
                 ) ->     None:
        """"""
        window = env.app.get_active_main_window()
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