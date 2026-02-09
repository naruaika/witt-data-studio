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

from .. import environment as env
from ..core.action import Action as _Action

from .content import NodeContent
from .editor import NodeEditor
from .frame import NodeFrame
from .link import NodeLink
from .socket import NodeSocket

class Action(_Action):

    def __init__(self,
                 owner: object = None, # Editor
                 coown: object = None, # Editor
                 ) ->   None:
        """"""
        super().__init__(owner, coown)

        window = env.app.get_active_main_window()
        self.owner = window.node_editor



class ActionAddNode(Action):

    def __init__(self,
                 editor: NodeEditor,
                 nodes:  list[NodeFrame],
                 ) ->    None:
        """"""
        super().__init__()

        self.editor = editor
        self.nodes  = copy(nodes)

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

        GLib.timeout_add(50, self.editor.do_collect_points, self.nodes)

        return True

    def undo(self) -> bool:
        """"""
        window = env.app.get_active_main_window()
        freezing = window.history.freezing
        window.history.freezing = True

        ActionDeleteNode(self.editor, self.nodes).do()

        window.history.freezing = freezing

        return True



class ActionDeleteNode(Action):

    def __init__(self,
                 editor: NodeEditor,
                 nodes:  list[NodeFrame],
                 ) ->    None:
        """"""
        super().__init__()

        self.editor = editor
        self.nodes  = copy(nodes)

        self.node_values     = []
        self.removed_links   = []
        self.removed_structs = []

    def do(self,
           undoable: bool = True,
           ) ->      bool:
        """"""
        for node in self.nodes:
            self.editor.nodes.remove(node)

            if node in self.editor.selected_nodes:
                self.editor.selected_nodes.remove(node)

            value = node.do_save()
            self.node_values.append(value)

            for content in node.contents:
                if not content.Socket:
                    continue

                for link in copy(content.Socket.links):
                    if link.in_socket.auto_remove:
                        frame = link.in_socket.Frame
                        content = link.in_socket.Content
                        cindex = frame.contents.index(content)
                        struct = (frame, content, cindex)
                        self.removed_structs.append(struct)

                    if link.out_socket.auto_remove:
                        frame = link.out_socket.Frame
                        content = link.out_socket.Content
                        cindex = frame.contents.index(content)
                        struct = (frame, content, cindex)
                        self.removed_structs.append(struct)

            for content in copy(node.contents):
                if not content.Socket:
                    continue

                for link in copy(content.Socket.links):
                    ActionDeleteLink(self.editor, link).do()
                    self.removed_links.append(link)

            node.unparent()

        gc.collect()

        GLib.timeout_add(50, self.editor.do_collect_points)

        return True

    def undo(self) -> bool:
        """"""
        window = env.app.get_active_main_window()
        freezing = window.history.freezing
        window.history.freezing = True

        ActionAddNode(self.editor, self.nodes).do()

        for index, value in enumerate(self.node_values):
            self.nodes[index].do_restore(value)

        for struct in self.removed_structs:
            frame, content, cindex = struct
            ActionDeleteNodeContent(self.editor, content, frame, cindex).undo()
            content.is_freezing = True

        for link in self.removed_links:
            ActionAddLink(self.editor, link.in_socket, link.out_socket).do()

        for struct in self.removed_structs:
            frame, content, cindex = struct
            content.is_freezing = False

        window.history.freezing = freezing

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
        self.nodes     = copy(nodes)
        self.positions = positions

    def do(self,
           undoable: bool = True,
           ) ->      bool:
        """"""
        canvas = self.editor.Canvas

        canvas_width  = canvas.get_width()
        canvas_height = canvas.get_height()

        for index, node in enumerate(self.nodes):
            node_width  = node.get_width()  or 175
            node_height = node.get_height() or 125
            max_x = canvas_width  - node_width
            max_y = canvas_height - node_height

            node.x = self.positions[index][1][0]
            node.y = self.positions[index][1][1]
            node.x = int(min(max(0, node.x), max_x))
            node.y = int(min(max(0, node.y), max_y))

            canvas.move(node, node.x, node.y)
            node.compute_points()

        self.editor.collect_points()

        gc.collect()

        return True

    def undo(self) -> bool:
        """"""
        window = env.app.get_active_main_window()
        freezing = window.history.freezing
        window.history.freezing = True

        positions = []
        for position in self.positions:
            positions.append((position[1], position[0]))

        ActionMoveNode(self.editor, self.nodes, positions).do()

        window.history.freezing = freezing

        return True



class ActionEditNode(Action):

    def __init__(self,
                 editor: NodeEditor,
                 node:   NodeFrame,
                 values: tuple,
                 ) ->    None:
        """"""
        super().__init__()

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



class ActionDeleteNodeContent(Action):

    def __init__(self,
                 editor:  NodeEditor,
                 content: NodeContent,
                 node:    NodeFrame = None,
                 cindex:  int       = None,
                 ) ->     None:
        """"""
        super().__init__()

        node = node or content.Frame

        if cindex is None:
            cindex = node.contents.index(content)

        self.editor  = editor
        self.content = content
        self.node    = node
        self.cindex  = cindex

    def do(self,
           undoable: bool = True,
           ) ->      bool:
        """"""
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



class ActionAddLink(Action):

    def __init__(self,
                 editor:  NodeEditor,
                 socket1: NodeSocket,
                 socket2: NodeSocket,
                 ) ->    None:
        """"""
        super().__init__()

        # Make sure the first socket is from a node output
        if socket1.is_input():
            socket1, socket2 = socket2, socket1

        self.editor  = editor
        self.socket1 = socket1
        self.socket2 = socket2
        self.frame2  = socket2.Frame

        self.new_link = None
        self.old_link = None
        self.old_data = None

    def do(self,
           undoable: bool = True,
           ) ->      bool:
        """"""
        # Skip if there's already a link between the two sockets
        for link in self.editor.links:
            if link.in_socket == self.socket1 and link.out_socket == self.socket2:
                return False

        # Keep track of the state of the target node
        # TODO: we should also track downstream nodes
        if self.socket2.links:
            self.old_data = self.frame2.do_save()

        # Unlink the target socket from a linkage if there is any
        # because it does not make sense to have multiple inputs.
        # Meanwhile, it makes sense to have multiple outputs from
        # a single socket from any node.
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

        # After undoing, a content that feature auto removal
        # will no longer available anywhere. Thus we need to
        # find the related placeholder socket, usually it is
        # the last socket of the node frame. Currently, only
        # the last socket that can be a placeholder so TODO?
        if self.socket2.Content not in self.frame2.contents:
            self.socket2 = self.frame2.contents[-1].Socket

        self.new_link = NodeLink(self.socket1, self.socket2).link()
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
        self.editor.links.append(self.link.link())

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



class ActionSelectByRubberband(Action):

    def __init__(self,
                 editor: NodeEditor,
                 combo:  bool = False,
                 ) ->    None:
        """"""
        super().__init__()

        self.editor = editor
        self.combo  = combo

        self.old_rubber_band    = None
        self.old_selected_nodes = []

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

    def isduplicate(self,
                    action: Action,
                    ) ->    bool:
        """"""
        return False # TODO
