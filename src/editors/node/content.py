# content.py
#
# Copyright 2025 Naufan Rusyda Faikar <hello@naruaika.me>
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

from gi.repository import Adw
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
                                    auto_remove) \
                         if socket_type else None

        self.placeholder = placeholder
        self.auto_remove = auto_remove

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

    def do_link(self,
                pair_socket:  'NodeSocket',
                self_content: 'NodeContent',
                ) ->          'None':
        """"""
        if self_content.Socket.is_input():
            self.Frame.do_execute(pair_socket, self_content)

    def do_unlink(self,
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
