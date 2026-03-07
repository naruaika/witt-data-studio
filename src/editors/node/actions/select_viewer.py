# select_viewer.py
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
from ....core.construct import Sheet

from ..editor import NodeEditor
from ..frame import NodeFrame

class ActionSelectViewer(Action):

    def __init__(self,
                 editor: NodeEditor,
                 viewer: NodeFrame,
                 ) ->    None:
        """"""
        window = env.app.get_active_main_window()
        owner = window.node_editor

        super().__init__(owner)

        self.editor     = editor
        self.new_viewer = viewer
        self.old_viewer = None

    def do(self,
           undoable: bool = True,
           ) ->      bool:
        """"""
        if not self.new_viewer:
            return False

        from ..factory import NodeViewer

        for node in self.editor.nodes:
            if not isinstance(node.parent, NodeViewer):
                continue
            if node.is_active():
                self.old_viewer = node
                break

        for node in self.editor.nodes:
            if not isinstance(node.parent, NodeViewer):
                continue
            node.set_active(node == self.new_viewer)

        if self.old_viewer == self.new_viewer:
            return False

        window = self.editor.get_window()
        tab_view = window.TabView

        n_pinned = tab_view.get_n_pinned_pages()
        n_pages = tab_view.get_n_pages() - n_pinned

        # Close all existing pages
        for _ in range(n_pages):
            page = tab_view.get_nth_page(n_pinned)
            tab_view.close_page(page)

        # Clean up page references
        if self.old_viewer:
            sviews = self.old_viewer.parent.SUPPORTED_VIEWS
            for content in self.old_viewer.contents[:-1]:
                socket = content.Socket
                if socket.data_type in sviews:
                    content.Page = None

        # Open all related pages
        parent = self.new_viewer.parent
        for self_content in self.new_viewer.contents[:-1]:
            self_socket = self_content.Socket
            link = self_socket.links[0]
            pair_socket = link.in_socket
            if pair_socket.data_type == Sheet:
                label = self_content.Widget
                title = label.get_label()
                args = (title, pair_socket, self_content)
                parent.add_sheet_editor(*args)

        return True

    def undo(self) -> bool:
        """"""
        if self.old_viewer:
            self.old_viewer.set_active(True)

        self.new_viewer.set_active(False)

        return True