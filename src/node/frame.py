# frame.py
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

from gi.repository import Adw
from gi.repository import Gdk
from gi.repository import Graphene
from gi.repository import Gtk
from typing import Any
from typing import TypeAlias

Point2D: TypeAlias = tuple[float, float]

@Gtk.Template(resource_path = '/com/macipra/witt/node/frame.ui')
class NodeFrame(Adw.Bin):

    __gtype_name__ = 'NodeFrame'

    Head  = Gtk.Template.Child()
    Title = Gtk.Template.Child()

    Body  = Gtk.Template.Child()

    def __init__(self,
                 title:  'str',
                 x:      'float'        = 0.0,
                 y:      'float'        = 0.0,
                 parent: 'NodeTemplate' = None,
                 ) ->    'None':
        """"""
        super().__init__(focusable = True)

        self.Title.set_label(title)

        self.x      = x
        self.y      = y
        self.parent = parent

        self.contents:    list['NodeContent'] = []
        self.in_points:   list['Point2D']     = []
        self.in_sockets:  list['NodeSocket']  = []
        self.out_points:  list['Point2D']     = []
        self.out_sockets: list['NodeSocket']  = []

        self.is_selected = False

        self.is_processing = False

        self._setup_controllers()

    def _setup_controllers(self) -> None:
        """"""
        self._click_handler = Gtk.GestureClick(button = Gdk.BUTTON_PRIMARY)
        self._click_handler.connect('pressed', self._on_lmb_pressed)
        self._click_handler.connect('released', self._on_lmb_released)
        self.add_controller(self._click_handler)

        self._drag_handler = Gtk.GestureDrag()
        self._drag_handler.connect('drag-begin', self._on_drag_begin)
        self._drag_handler.connect('drag-update', self._on_drag_update)
        self._drag_handler.connect('drag-end', self._on_drag_end)
        self.add_controller(self._drag_handler)

    def _on_lmb_pressed(self,
                        gesture: Gtk.GestureClick,
                        n_press: int,
                        x:       float,
                        y:       float,
                        ) ->     None:
        """"""
        state = gesture.get_current_event_state()
        combo = state & Gdk.ModifierType.SHIFT_MASK != 0

        if not combo and self.is_selected:
            return

        editor = self.get_editor()
        editor.select_by_click(self, combo)
        self.grab_focus()

        # Raise the widget to the top
        top_widget = editor.Canvas.get_last_child()
        if top_widget != self:
            self.insert_after(editor.Canvas, top_widget)

        # Calculate maximum position to prevent the nodes
        # from go beyond the canvas boundaries which will
        # make them no longer accessible
        parent = self.get_parent()
        frame_width = self.get_width()
        frame_height = self.get_height()
        parent_width = parent.get_width()
        parent_height = parent.get_height()
        self._max_x = parent_width - frame_width
        self._max_y = parent_height - frame_height

        # Prevent from triggering the released event
        gesture.set_state(Gtk.EventSequenceState.DENIED)

    def _on_lmb_released(self,
                         gesture: Gtk.GestureClick,
                         n_press: int,
                         x:       float,
                         y:       float,
                         ) ->     None:
        """"""
        editor = self.get_editor()
        state = gesture.get_current_event_state()
        combo = state & Gdk.ModifierType.SHIFT_MASK != 0
        editor.select_by_click(self, combo)
        self.grab_focus()

        # Raise the widget to the top
        top_widget = editor.Canvas.get_last_child()
        if top_widget != self:
            self.insert_after(editor.Canvas, top_widget)

    def _on_drag_begin(self,
                       gesture: Gtk.GestureDrag,
                       start_x: float,
                       start_y: float,
                       ) ->     None:
        """"""
        editor = self.get_editor()
        editor.begin_move_selections()

    def _on_drag_update(self,
                        gesture:  Gtk.GestureDrag,
                        offset_x: float,
                        offset_y: float,
                        ) ->      None:
        """"""
        editor = self.get_editor()
        editor.update_move_selections(offset_x, offset_y)

        # Prevent from triggering the released event.
        # We add threshold to ignore slight movement.
        if abs(offset_x) > 0.5 and abs(offset_y) > 0.5:
            self._click_handler.set_state(Gtk.EventSequenceState.DENIED)

    def _on_drag_end(self,
                     gesture:  Gtk.GestureDrag,
                     offset_x: float,
                     offset_y: float,
                     ) ->      None:
        """"""
        editor = self.get_editor()
        editor.end_move_selections()

    def set_data(self, *args, **kwargs) -> None:
        """"""
        pass

    def do_execute(self,
                   pair_socket:  'NodeSocket'  = None,
                   self_content: 'NodeContent' = None,
                   backward:     'bool'        = True,
                   forward:      'bool'        = True,
                   specified:    'bool'        = False,
                   ) ->          'None':
        """"""
        if self.is_processing:
            return

        if self_content:
            self_socket = self_content.Socket

        if backward:
            visited_frames = []
            for content in self.contents:
                if not (socket := content.Socket):
                    continue
                if not socket.is_input():
                    continue
                if (
                    specified              and
                    self_content           and
                    self_socket.is_input() and
                    self_content != content
                ):
                    continue
                for link in socket.links:
                    if not link.compatible:
                        continue
                    frame = link.in_socket.Frame
                    if frame in visited_frames:
                        continue
                    frame.do_execute(socket,
                                     self_content,
                                     forward = False)
                    visited_frames.append(frame)
            del visited_frames

        self.do_process(pair_socket, self_content)

        if forward:
            visited_frames = []
            for content in self.contents:
                if not (socket := content.Socket):
                    continue
                if not socket.is_output():
                    continue
                if (
                    specified               and
                    self_content            and
                    self_socket.is_output() and
                    self_content != content
                ):
                    continue
                for link in socket.links:
                    if not link.compatible:
                        continue
                    frame = link.out_socket.Frame
                    if frame in visited_frames:
                        continue
                    frame.do_execute(socket,
                                     self_content,
                                     backward = False)
                    visited_frames.append(frame)
            del visited_frames

    def do_process(self,
                   pair_socket:  'NodeSocket',
                   self_content: 'NodeContent',
                   ) ->          'None':
        """"""
        # It's more safe to set self.is_processing = True
        # before calling NodeContent.set_data(). Then set
        # it back to False. It would mostly can help with
        # recursion issues.
        pass

    def do_save(self) -> Any:
        """"""
        value = None
        return value

    def do_restore(self,
                   value: Any,
                   ) ->   None:
        """"""
        pass

    def add_content(self,
                    widget:      'Gtk.Widget'     = None,
                    socket_type: 'NodeSocketType' = None,
                    data_type:   'Any'            = None,
                    get_data:    'callable'       = None,
                    set_data:    'callable'       = None,
                    placeholder: 'bool'           = False,
                    auto_remove: 'bool'           = False,
                    ) ->         'NodeContent':
        """"""
        if not widget:
            widget = Gtk.Label(label   = _('Value'),
                               xalign  = 0.0,
                               opacity = 0.0)

        if not get_data:
            get_data = lambda *_: None
        if not set_data:
            set_data = lambda *_: None

        content = NodeContent(self,
                              widget,
                              socket_type,
                              data_type,
                              get_data,
                              set_data,
                              placeholder,
                              auto_remove)
        self.Body.append(content.Container)
        self.contents.append(content)

        return content

    def remove_content(self,
                       content: 'NodeContent',
                       ) ->     'None':
        """"""
        editor = self.get_editor()

        if content.Socket:
            for link in content.Socket.links:
                if link not in editor.links:
                    continue
                editor.links.remove(link)
                if link.in_socket.auto_remove:
                    content = link.in_socket.Content
                    content.do_remove(content)
                if link.out_socket.auto_remove:
                    content = link.out_socket.Content
                    content.do_remove(content)
                link.unlink()

        content.Container.unparent()
        if content in self.contents:
            self.contents.remove(content)

    def compute_points(self) -> None:
        """"""
        self.in_sockets  = []
        self.in_points   = []
        self.out_sockets = []
        self.out_points  = []

        editor = self.get_editor()
        canvas = editor.Canvas

        ref_point = Graphene.Point().init(0, 0)

        radius = 6 # socket radius is always 6px

        for content in self.contents:
            socket = content.Socket

            if not socket:
                continue

            *_, point = socket.compute_point(canvas, ref_point)
            point = (point.x + radius - 2, point.y + radius)

            if socket.is_input():
                self.in_points.append(point)
                self.in_sockets.append(socket)

            if socket.is_output():
                self.out_points.append(point)
                self.out_sockets.append(socket)

    def select(self) -> None:
        """"""
        editor = self.get_editor()
        if self not in editor.selected_nodes:
            editor.selected_nodes.append(self)
        self.add_css_class('selected')
        self.is_selected = True

    def unselect(self) -> None:
        """"""
        editor = self.get_editor()
        if self in editor.selected_nodes:
            editor.selected_nodes.remove(self)
        self.remove_css_class('selected')
        self.is_selected = False

    def toggle(self) -> None:
        """"""
        editor = self.get_editor()
        if self.has_css_class('selected'):
            self.remove_css_class('selected')
            if self in editor.selected_nodes:
                editor.selected_nodes.remove(self)
            self.is_selected = False
        else:
            self.add_css_class('selected')
            if self not in editor.selected_nodes:
                editor.selected_nodes.append(self)
            self.is_selected = True

    def get_editor(self) -> 'NodeEditor':
        """"""
        canvas = self.get_parent()
        viewport = canvas.get_parent()
        scrolled_window = viewport.get_parent()
        editor = scrolled_window.get_parent()
        return editor

from .editor import NodeEditor
from .content import NodeContent
from .socket import NodeSocket
from .socket import NodeSocketType
from .repository import NodeTemplate
