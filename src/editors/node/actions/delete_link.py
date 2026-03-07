# delete_link.py
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
from ..link import NodeLink

class ActionDeleteLink(Action):

    def __init__(self,
                 editor: NodeEditor,
                 link:   NodeLink,
                 ) ->    None:
        """"""
        window = env.app.get_active_main_window()
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