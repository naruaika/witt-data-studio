# action.py
#
# Copyright (c) 2025 Naufan Rusyda Faikar
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
import gc

from .editor import NodeEditor
from .frame import NodeFrame
from .link import NodeLink
from .socket import NodeSocket

from ..core.action import Action

class ActionAddNode(Action):

    def __init__(self,
                 editor: NodeEditor,
                 nodes:  list[NodeFrame],
                 ) ->    None:
        """"""
        super().__init__()

        self.editor = editor
        self.nodes  = nodes

    def do(self,
           undoable: bool = True,
           ) ->      bool:
        """"""
        for node in self.nodes:
            self.editor.Canvas.put(node, node.x, node.y)
            self.editor.nodes.append(node)

            if node.is_selected:
                self.editor.selected_nodes.append(node)

            from .repository import NodeViewer
            if isinstance(node.parent, NodeViewer):
                ActionSelectViewer(self.editor, node).do()

        # TODO: scroll to the newly added node
        # if the editor is in view, especially
        # if that node is automatically linked
        # and arranged (not at random places).
        # Calling Gtk.Viewport.scroll_to() did
        # not solve the problem unless delayed
        # by a proper timing in which can't be
        # sure to always works.

        GLib.idle_add(self.editor.do_collect_points, self.nodes)

        return True

    def undo(self) -> bool:
        """"""
        freezing = self.editor.history.freezing
        self.editor.history.freezing = True

        ActionDeleteNode(self.editor, self.nodes).do()

        self.editor.history.freezing = freezing

        return True



class ActionDeleteNode(Action):

    def __init__(self,
                 editor: NodeEditor,
                 nodes:  list[NodeFrame],
                 ) ->    None:
        """"""
        super().__init__()

        self.editor = editor
        self.nodes  = nodes

    def do(self,
           undoable: bool = True,
           ) ->      bool:
        """"""
        for node in self.nodes:
            self.editor.nodes.remove(node)

            if node in self.editor.selected_nodes:
                self.editor.selected_nodes.remove(node)

            for content in node.contents:
                if not content.Socket:
                    continue

                for link in content.Socket.links:
                    ActionDeleteLink(self.editor, link).do()

            node.unparent()

        gc.collect()

        GLib.idle_add(self.editor.do_collect_points)

        return True

    def undo(self) -> bool:
        """"""
        freezing = self.editor.history.freezing
        self.editor.history.freezing = True

        ActionAddNode(self.editor, self.nodes).do()

        self.editor.history.freezing = freezing

        return True



class ActionMoveNode(Action):

    def __init__(self,
                 editor:    NodeEditor,
                 nodes:     list[NodeFrame],
                 positions: list[tuple],
                 ) ->       None:
        """"""
        super().__init__()

        self.editor    = editor
        self.nodes     = nodes
        self.positions = positions

    def do(self,
           undoable: bool = True,
           ) ->      bool:
        """"""
        canvas = self.editor.Canvas

        for index, node in enumerate(self.nodes):
            node.x = self.positions[index][1][0]
            node.y = self.positions[index][1][1]
            canvas.move(node, node.x, node.y)
            node.compute_points()

        self.editor.collect_points()

        gc.collect()

        return True

    def undo(self) -> bool:
        """"""
        freezing = self.editor.history.freezing
        self.editor.history.freezing = True

        positions = []
        for position in self.positions:
            positions.append((position[1], position[0]))

        ActionMoveNode(self.editor, self.nodes, positions).do()

        self.editor.history.freezing = freezing

        return True



class ActionAddLink(Action):

    def __init__(self,
                 editor:  NodeEditor,
                 socket1: NodeSocket,
                 socket2: NodeSocket,
                 ) ->    None:
        """"""
        super().__init__()

        self.editor   = editor
        self.socket1  = socket1
        self.socket2  = socket2

        self.frame2   = socket2.Frame

        self.new_link = None
        self.old_link = None

    def do(self,
           undoable: bool = True,
           ) ->      bool:
        """"""
        # Make sure the first socket is from a node output
        if self.socket1.is_input():
            self.socket1, self.socket2 = self.socket2, self.socket1

        # Skip if there's already a link between the two sockets
        for link in self.editor.links:
            if link.in_socket == self.socket1 and link.out_socket == self.socket2:
                return False

        # Unlink the target socket from a linkage if there is any
        # because it does not make sense to have multiple inputs.
        # Meanwhile, it makes sense to have multiple outputs from
        # a single socket from any node.
        if self.socket2.links:
            self.old_link = self.socket2.links[0].unlink()
            self.editor.links.remove(self.old_link)

        # After undoing, a content that feature auto removal
        # will no longer available anywhere. Thus we need to
        # find the related placeholder socket, usually it is
        # the last socket of the node frame. Currently, only
        # the last socket that can be a placeholder so TODO?
        if self.socket2.Content not in self.frame2.contents:
            self.socket2 = self.frame2.contents[-1].Socket

        self.new_link = NodeLink(self.socket1, self.socket2).link()
        self.editor.links.append(self.new_link)

        nodes = [self.socket1.Frame, self.socket2.Frame]
        GLib.idle_add(self.editor.do_collect_points, nodes)

        return True

    def undo(self) -> bool:
        """"""
        freezing = self.editor.history.freezing
        self.editor.history.freezing = True

        if self.old_link:
            self.editor.links.remove(self.new_link.unlink())
            self.editor.links.append(self.old_link.link())

        else:
            ActionDeleteLink(self.editor, self.new_link).do()

        self.editor.history.freezing = freezing

        return True



class ActionDeleteLink(Action):

    def __init__(self,
                 editor: NodeEditor,
                 link:   NodeLink,
                 ) ->    None:
        """"""
        super().__init__()

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
        freezing = self.editor.history.freezing
        self.editor.history.freezing = True

        socket1 = self.link.in_socket
        socket2 = self.link.out_socket
        ActionAddLink(self.editor, socket1, socket2).do()

        self.editor.history.freezing = freezing

        return True



class ActionSelectViewer(Action):

    def __init__(self,
                 editor: NodeEditor,
                 viewer: NodeFrame,
                 ) ->    None:
        """"""
        super().__init__()

        self.editor     = editor
        self.new_viewer = viewer
        self.old_viewer = None

    def do(self,
           undoable: bool = True,
           ) ->      bool:
        """"""
        from .repository import NodeViewer

        for node in self.editor.nodes:
            if not isinstance(node.parent, NodeViewer):
                continue
            if node == self.new_viewer:
                node.set_active(True)
                continue
            if node.is_active():
                self.old_viewer = node
                node.set_active(False)

        # TODO: update window.TabView

        return True

    def undo(self) -> bool:
        """"""
        if self.old_viewer:
            self.old_viewer.set_active(True)

        self.new_viewer.set_active(False)

        return True


class ActionSelectByClick(Action):

    def __init__(self,
                 editor: NodeEditor,
                 node:   NodeFrame = None,
                 combo:  bool      = False,
                 ) ->    None:
        """"""
        super().__init__()

        self.editor = editor
        self.node   = node
        self.combo  = combo

    def do(self,
           undoable: bool = True,
           ) ->      bool:
        """"""
        from .repository import NodeViewer

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

        if self.node:
            if isinstance(self.node.parent, NodeViewer):
                ActionSelectViewer(self.editor, self.node).do()

        return True

    def undo(self) -> bool:
        """"""
        while self.editor.selected_nodes:
            node = self.editor.selected_nodes[0]
            node.unselect()

        for node in self.old_selected_nodes:
            node.select()

        return True



class ActionSelectByRubberband(Action):

    def __init__(self,
                 editor: NodeEditor,
                 combo:  bool = False,
                 ) ->    None:
        """"""
        super().__init__()

        self.editor = editor
        self.combo  = combo

        self.old_rubber_band = None

    def do(self,
           undoable: bool = True,
           ) ->      bool:
        """"""
        self.old_selected_nodes = copy(self.editor.selected_nodes)

        if not self.combo:
            while self.editor.selected_nodes:
                node = self.editor.selected_nodes[0]
                node.unselect()

        if self.old_rubber_band:
            self.editor.rubber_band = copy(self.old_rubber_band)
        else:
            self.old_rubber_band = copy(self.editor.rubber_band)

        p1, p2 = self.editor.rubber_band
        x1, y1 = p1
        x2, y2 = p2

        sel_x      = min(x1, x2)
        sel_y      = min(y1, y2)
        sel_width  = abs(x1 - x2)
        sel_height = abs(y1 - y2)

        sel_right  = sel_x + sel_width
        sel_bottom = sel_y + sel_height

        for node in self.editor.nodes:
            allocation = node.get_allocation()

            node_x      = allocation.x
            node_y      = allocation.y
            node_width  = allocation.width
            node_height = allocation.height

            node_right  = node_x + node_width
            node_bottom = node_y + node_height

            if (
                sel_x      < node_right  and
                sel_right  > node_x      and
                sel_y      < node_bottom and
                sel_bottom > node_y
            ):
                node.toggle()

        self.editor.rubber_band = None

        return True

    def undo(self) -> bool:
        """"""
        while self.editor.selected_nodes:
            node = self.editor.selected_nodes[0]
            node.unselect()

        for node in self.old_selected_nodes:
            node.select()

        return True
