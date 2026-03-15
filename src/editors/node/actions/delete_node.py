# delete_node.py
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
from gi.repository import GLib
import gc

from .... import environment as env
from ....core.action import Action

from ..editor import NodeEditor
from ..frame import NodeFrame

class ActionDeleteNode(Action):

    def __init__(self,
                 editor: NodeEditor,
                 nodes:  list[NodeFrame],
                 ) ->    None:
        """"""
        window = env.app.get_active_main_window()
        owner = window.node_editor

        super().__init__(owner)

        self.editor = editor
        self.nodes  = copy(nodes)

        self.node_values     = []
        self.removed_links   = []
        self.removed_structs = []

    def do(self,
           undoable: bool = True,
           ) ->      bool:
        """"""
        if not self.nodes:
            return False

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
            action = ActionDeleteContent(self.editor,
                                             content,
                                             frame,
                                             cindex)
            action.undo()
            content.is_freezing = True

        for link in self.removed_links:
            action = ActionAddLink(self.editor,
                                   link.in_socket,
                                   link.out_socket)
            action.do()

        for struct in self.removed_structs:
            frame, content, cindex = struct
            content.is_freezing = False

        window.history.freezing = freezing

        return True

from .add_link import *
from .add_node import *
from .delete_content import *
from .delete_link import *