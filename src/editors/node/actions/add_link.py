# add_link.py
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

from gi.repository import GLib

from .... import environment as env
from ....core.action import Action

from ..editor import NodeEditor
from ..link import NodeLink
from ..socket import NodeSocket

class ActionAddLink(Action):

    def __init__(self,
                 editor:  NodeEditor,
                 socket1: NodeSocket,
                 socket2: NodeSocket,
                 ) ->    None:
        """"""
        window = env.app.get_active_main_window()
        owner = window.node_editor

        super().__init__(owner)

        # Make sure the first socket is from a node output
        if socket1.is_input():
            socket1, socket2 = socket2, socket1

        self.editor  = editor
        self.socket1 = socket1
        self.socket2 = socket2
        self.frame2  = socket2.Frame

        self.new_content = None
        self.new_link    = None
        self.new_data    = None
        self.old_link    = None
        self.old_data    = None

    def do(self,
           undoable: bool = True,
           ) ->      bool:
        """"""
        # Skip if there is already a link
        for link in self.editor.links:
            if (
                link.in_socket  == self.socket1 and
                link.out_socket == self.socket2
            ):
                return False

        # Keep track of the state of the target node
        # TODO: we should also track downstream nodes
        if self.socket2.links:
            self.old_data = self.frame2.do_save()

        # Unlink the target socket from a linkage if
        # there is any because it doesn't make sense
        # to have multiple inputs. Meanwhile it does
        # make sense to have multiple outputs from a
        # single socket from any node.
        if self.socket2.links:
            link = self.socket2.links[0]
            self.old_link = link.unlink()
            self.editor.links.remove(self.old_link)

        # We flag the target content as frozen so that
        # it can be properly handled when doing a link
        # for instance to prevent from auto generation
        # of the socket label like in NodeSheet.
        if self.old_link:
            content = self.old_link.out_socket.Content
            content.is_freezing = True

        # Restore the link from previous state before
        # undoing as well as the exact content if any
        if self.new_link:
            if self.new_content:
                last_container = self.frame2.Body.get_last_child()
                last_container.unparent()
                self.frame2.Body.append(self.new_content.Container)
                self.frame2.Body.append(last_container)

                self.frame2.contents.insert(-1, self.new_content)
                self.socket2 = self.new_content.Socket

            if self.new_data:
                self.frame2.do_restore(self.new_data)

            self.new_link.link()

            if self.old_link:
                content.is_freezing = False

        else:
            self.new_link = NodeLink(self.socket1, self.socket2)
            self.new_link.link()

            if self.old_link:
                self.new_data = self.frame2.do_save()

            if self.socket2.placeholder:
                self.new_content = self.socket2.Content
                self.new_data = self.frame2.do_save()

        self.editor.links.append(self.new_link)

        if self.old_link:
            content = self.old_link.out_socket.Content
            content.is_freezing = False

        nodes = [self.socket1.Frame, self.socket2.Frame]
        GLib.timeout_add(50, self.editor.do_collect_points, nodes)

        return True

    def undo(self) -> bool:
        """"""
        window = env.app.get_active_main_window()
        freezing = window.history.freezing
        window.history.freezing = True

        if self.old_link:
            content = self.old_link.out_socket.Content
            content.is_freezing = True

            self.editor.links.remove(self.new_link.unlink())
            self.frame2.do_restore(self.old_data)
            self.editor.links.append(self.old_link.link())

            content.is_freezing = False

        else:
            ActionDeleteLink(self.editor, self.new_link).do()

        window.history.freezing = freezing

        return True

from .delete_link import *