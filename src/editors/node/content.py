# content.py
#
# Copyright 2025 Naufan Rusyda Faikar <hello@naruaika.me>
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

from gi.repository import Gtk
from typing import Any

import gc

class NodeContent(Gtk.Widget):

    __gtype_name__ = 'NodeContent'

    def __init__(self,
                 frame:       'NodeFrame',
                 widget:      'Gtk.Widget',
                 socket_type: 'NodeSocketType' = None,
                 data_type:   'Any'            = None,
                 get_data:    'callable'       = None,
                 set_data:    'callable'       = None,
                 placeholder: 'bool'           = False,
                 auto_remove: 'bool'           = False,
                 auto_update: 'bool'           = False,
                 ) ->         'None':
        """"""
        super().__init__()

        self.Frame     = frame
        self.Container = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL)
        self.Widget    = widget
        self.Socket    = NodeSocket(self,
                                    socket_type,
                                    data_type,
                                    placeholder,
                                    auto_remove,
                                    auto_update) \
                         if socket_type else None

        self.placeholder = placeholder
        self.auto_remove = auto_remove
        self.auto_update = auto_update

        self.is_freezing = False

        # For external usage
        self.get_data = get_data or (lambda *_: None)
        self.set_data = set_data or (lambda *_: None)
        self.Page     = None
        self.node_uid = None # pair node cache

        if socket_type == NodeSocketType.INPUT:
            self.Container.append(self.Socket)
        self.Container.append(widget)
        if socket_type == NodeSocketType.OUTPUT:
            self.Container.append(self.Socket)

        self.add_css_class('node-content')
        widget.add_css_class('node-widget')
        if socket_type == NodeSocketType.INPUT:
            widget.add_css_class('after-socket')
        if socket_type == NodeSocketType.OUTPUT:
            widget.add_css_class('before-socket')

        widget.set_hexpand(True)

    def post_link(self) -> None:
        """"""
        self.placeholder = False
        self.Socket.placeholder = False

    def do_link(self,
                pair_socket:  'NodeSocket',
                self_content: 'NodeContent',
                ) ->          'None':
        """"""
        if not self_content.Socket.is_input():
            return

        from .factory._utils import iscompatible
        if not iscompatible(pair_socket, self_content):
            return

        self.Frame.do_execute(pair_socket, self_content)

    def do_unlink(self,
                  socket: 'NodeSocket',
                  ) ->    'None':
        """"""
        if socket.is_input():
            self.Frame.do_execute(self_content = socket.Content,
                                  backward     = False)

    def do_update(self,
                  socket: 'NodeSocket',
                  ) ->    'None':
        """"""
        if socket.is_input():
            self.Frame.do_execute(self_content = socket.Content)

    def do_remove(self,
                  content: 'NodeContent',
                  ) ->     'None':
        """"""
        self.node_uid = None
        self.Frame.remove_content(content)
        gc.collect()

from .frame import NodeFrame
from .socket import NodeSocket
from .socket import NodeSocketType
