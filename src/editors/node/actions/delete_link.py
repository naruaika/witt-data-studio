# delete_link.py
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

from ..editor import NodeEditor
from ..link   import NodeLink

class ActionDeleteLink(Action):

    def __init__(self,
                 editor: NodeEditor,
                 link:   NodeLink,
                 ) ->    None:
        """"""
        window = env.APP.get_active_main_window()
        owner = window.node_editor

        super().__init__(owner)

        self.editor = editor
        self.link   = link

    def do(self,
           undoable: bool = True,
           ) ->      bool:
        """"""
        if self.link in self.editor.links:
            self.editor.links.remove(self.link)

        if self.link.in_socket.auto_remove:
            content = self.link.in_socket.Content
            content.do_remove(content)

        if self.link.out_socket.auto_remove:
            content = self.link.out_socket.Content
            content.do_remove(content)

        self.link.unlink()

        return True

    def undo(self) -> bool:
        """"""
        link = self.link.link()
        self.editor.links.append(link)

        return True