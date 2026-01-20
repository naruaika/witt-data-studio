# socket.py
#
# Copyright 2025 Naufan Rusyda Faikar
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

from enum import Enum
from gi.repository import Gdk
from gi.repository import Graphene
from gi.repository import Gtk
from typing import Any

class NodeSocketType(Enum):

    INPUT  = 1
    OUTPUT = 2



class NodeSocket(Gtk.Widget):

    __gtype_name__ = 'NodeSocket'

    def __init__(self,
                 content:     'NodeContent',
                 socket_type: 'NodeSocketType',
                 data_type:   'Any',
                 placeholder: 'bool' = False,
                 auto_remove: 'bool' = False,
                 ) ->         'None':
        """"""
        super().__init__(halign = Gtk.Align.CENTER,
                         valign = Gtk.Align.CENTER)

        self.set_size_request(12, 12)

        self.add_css_class('node-socket')
        if socket_type == NodeSocketType.INPUT:
            self.add_css_class('socket-input')
        if socket_type == NodeSocketType.OUTPUT:
            self.add_css_class('socket-output')

        fallback = Gdk.Cursor.new_from_name('default')
        cursor = Gdk.Cursor.new_from_name('crosshair', fallback)
        self.set_cursor(cursor)

        self.Content:     'NodeContent'      = content
        self.socket_type: 'NodeSocketType'   = socket_type
        self.data_type:   'Any'              = data_type
        self.links:       'list'['NodeLink'] = []

        self.Frame:       'NodeFrame'        = content.Frame
        self.placeholder: 'bool'             = placeholder
        self.auto_remove: 'bool'             = auto_remove

        self._setup_controllers()

    def _setup_controllers(self) -> None:
        """"""
        controller = Gtk.GestureDrag()
        controller.connect('drag-begin', self._on_drag_begin)
        controller.connect('drag-update', self._on_drag_update)
        controller.connect('drag-end', self._on_drag_end)
        self.add_controller(controller)

    def _on_drag_begin(self,
                       gesture: Gtk.GestureDrag,
                       start_x: float,
                       start_y: float,
                       ) ->     None:
        """"""
        canvas = self.get_canvas()
        editor = self.get_editor()

        source_socket = self
        # If it is a second socket and is already in link,
        # edit that linkage virtually instead
        is_outsocket = self.is_input()
        is_connected = len(self.links) == 1
        if is_outsocket and is_connected:
            link = self.links[0]
            source_socket = link.in_socket

        radius = 6 # socket radius is always 6px

        # Compute the socket coordinate relative to the canvas
        point = Graphene.Point().init(0, 0)
        *_, point = source_socket.compute_point(canvas, point)
        point = (point.x + radius - 2, point.y + radius)
        scalar = (point, point)

        self._offset = (0, 0)
        # We need to also offset the future-link's end
        # when vritually editing an existing linkage
        if is_outsocket and is_connected:
            point = Graphene.Point().init(0, 0)
            *_, point = self.compute_point(canvas, point)
            point = (point.x + radius - 2, point.y + radius)
            scalar = (scalar[0], point)
            self._offset = (point[0] - scalar[0][0],
                            point[1] - scalar[0][1])

        # Do not forget to also unlink the actual linkage
        if is_outsocket and is_connected:
            editor.links.remove(link)
            if self.auto_remove:
                editor.removed_socket = self
            link.unlink()

        editor.begin_future_link(scalar, source_socket)

        # Prevent the gesture event listener on the node
        # frame from being triggered
        gesture.set_state(Gtk.EventSequenceState.CLAIMED)

    def _on_drag_update(self,
                        gesture:  Gtk.GestureDrag,
                        offset_x: float,
                        offset_y: float,
                        ) ->      None:
        """"""
        editor = self.get_editor()
        point_1 = editor.future_link[0]
        point_2 = (point_1[0] + self._offset[0] + offset_x,
                   point_1[1] + self._offset[1] + offset_y)
        scalar = (point_1, point_2)
        editor.update_future_link(scalar)

    def _on_drag_end(self,
                     gesture:  Gtk.GestureDrag,
                     offset_x: float,
                     offset_y: float,
                     ) ->      None:
        """"""
        editor = self.get_editor()
        editor.end_future_link()

    def is_input(self) -> bool:
        """"""
        return self.socket_type == NodeSocketType.INPUT

    def is_output(self) -> bool:
        """"""
        return self.socket_type == NodeSocketType.OUTPUT

    def get_canvas(self) -> 'NodeCanvas':
        """"""
        frame = self.Content.Frame
        canvas = frame.get_parent()
        return canvas

    def get_editor(self) -> 'NodeEditor':
        """"""
        canvas = self.get_canvas()
        viewport = canvas.get_parent()
        scrolled_window = viewport.get_parent()
        editor = scrolled_window.get_parent()
        return editor

from .editor import NodeEditor
from .canvas import NodeCanvas
from .frame import NodeFrame
from .content import NodeContent
from .link import NodeLink
