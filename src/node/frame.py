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

from enum import Enum
from gi.repository import Adw
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import Graphene
from gi.repository import Gtk
from typing import Any
from typing import TypeAlias

Point2D: TypeAlias = tuple[float, float]

class NodeFrameType(Enum):

    BRANCH = 3
    SOURCE = 1
    TARGET = 2


@Gtk.Template(resource_path = '/com/macipra/witt/node/frame.ui')
class NodeFrame(Adw.Bin):

    __gtype_name__ = 'NodeFrame'

    Head         = Gtk.Template.Child()
    Title        = Gtk.Template.Child()
    Body         = Gtk.Template.Child()
    ActiveToggle = Gtk.Template.Child()

    def __init__(self,
                 title:     'str',
                 x:         'float'         = 0.0,
                 y:         'float'         = 0.0,
                 parent:    'NodeTemplate'  = None,
                 node_type: 'NodeFrameType' = None,
                 ) ->       'None':
        """"""
        super().__init__(focusable = True)

        self.Title.set_label(title)
        self.Title.set_tooltip_text(title)

        self.x         = x
        self.y         = y
        self.parent    = parent
        self.node_type = node_type or NodeFrameType.BRANCH

        self.contents:    list['NodeContent'] = []
        self.in_points:   list['Point2D']     = []
        self.in_sockets:  list['NodeSocket']  = []
        self.out_points:  list['Point2D']     = []
        self.out_sockets: list['NodeSocket']  = []

        self.is_selected = False
        self.is_dragging = False
        self.is_clicking = False

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
        self.is_clicking = False

        state = gesture.get_current_event_state()
        combo = state & Gdk.ModifierType.SHIFT_MASK != 0

        if not combo and self.is_selected:
            return

        self.grab_focus()

        editor = self.get_editor()

        picked = self.pick(x, y, Gtk.PickFlags.DEFAULT)
        if (
            not picked.get_ancestor(Gtk.CheckButton) and
            not picked.get_ancestor(Gtk.Button)      and
            not picked.get_ancestor(Gtk.Expander)
        ):
            editor.select_by_click(self, combo)

        # Raise the widget to the top
        top_widget = editor.Canvas.get_last_child()
        if top_widget != self:
            self.insert_after(editor.Canvas, top_widget)

        parent = self.get_parent()

        frame_width   = self.get_width()
        frame_height  = self.get_height()
        parent_width  = parent.get_width()
        parent_height = parent.get_height()

        # Calculate maximum position to prevent the nodes
        # from go beyond the canvas boundaries which will
        # make them no longer accessible
        self._max_x = parent_width  - frame_width
        self._max_y = parent_height - frame_height
        self._old_x = self.x
        self._old_y = self.y

        # Prevent from triggering the released event
        self.is_clicking = True

    def _on_lmb_released(self,
                         gesture: Gtk.GestureClick,
                         n_press: int,
                         x:       float,
                         y:       float,
                         ) ->     None:
        """"""
        if self.is_clicking:
            self.is_clicking = False
            return

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
        if not self.is_dragging and \
                abs(offset_x) > 0.5 and \
                abs(offset_y) > 0.5:
            # Prevent from triggering the released event
            self._click_handler.set_state(Gtk.EventSequenceState.DENIED)

            # Block click gestures to reach children
            self.Body.set_sensitive(False)
            self.Body.set_sensitive(True)

            # Select itself if it isn't already
            if not self.is_selected:
                editor = self.get_editor()
                state = gesture.get_current_event_state()
                combo = state & Gdk.ModifierType.SHIFT_MASK != 0
                editor.select_by_click(self, combo)
                self.grab_focus()

            self.is_dragging = True

        state = gesture.get_current_event_state()
        snap = state & Gdk.ModifierType.CONTROL_MASK

        editor = self.get_editor()
        editor.update_move_selections(offset_x, offset_y, snap)

    def _on_drag_end(self,
                     gesture:  Gtk.GestureDrag,
                     offset_x: float,
                     offset_y: float,
                     ) ->      None:
        """"""
        self.is_dragging = False

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
                   initiator:    'bool'        = True,
                   ) ->          'None':
        """"""
        if self.is_processing:
            return

        if self_content:
            self_socket = self_content.Socket

        # Process parent frames
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
                    frame.do_execute(pair_socket  = socket,
                                     self_content = self_content,
                                     forward      = False,
                                     initiator    = False)
                    visited_frames.append(frame)

        # Get data from parent frames
        self.is_processing = True
        for content in self.contents:
            if not (self_socket := content.Socket):
                continue
            if not self_socket.is_input():
                continue
            if not (links := self_socket.links):
                continue
            if not links[0].compatible:
                continue
            psocket = links[0].in_socket
            pcontent = psocket.Content
            value = pcontent.get_data()
            content.set_data(value)
        self.is_processing = False

        self.do_process(pair_socket, self_content)

        # Collect all target frames and prevent
        # them from being processed right away.
        targets = set()
        is_target = self.node_type != NodeFrameType.TARGET
        if forward and initiator and is_target:
            self._collect_targets(targets)
        for frame, socket in targets:
            frame.is_processing = True

        # Process child frames
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
                    frame.do_execute(pair_socket  = socket,
                                     self_content = self_content,
                                     backward     = False,
                                     initiator    = False)
                    visited_frames.append(frame)

        # Process all target frames
        for frame, socket in targets:
            frame.is_processing = False
            frame.do_execute(pair_socket  = socket,
                             self_content = self_content,
                             backward     = False,
                             initiator    = False)

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

    def _collect_targets(self,
                         targets: 'set',
                         socket:  'NodeSocket' = None,
                         ) ->     'None':
        """"""
        if self.node_type == NodeFrameType.TARGET:
            targets.add((self, socket))
            return

        visited_frames = []
        for content in self.contents:
            if not (socket := content.Socket):
                continue
            if not socket.is_output():
                continue
            for link in socket.links:
                if not link.compatible:
                    continue
                frame = link.out_socket.Frame
                if frame in visited_frames:
                    continue
                frame._collect_targets(targets, socket)
                visited_frames.append(frame)

    def do_save(self) -> Any:
        """"""
        return None

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
        content.Container.unparent()
        if content in self.contents:
            self.contents.remove(content)

        editor = self.get_editor()

        if not editor:
            return

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

    def compute_points(self) -> None:
        """"""
        editor = self.get_editor()

        if not editor:
            return

        canvas = editor.Canvas

        self.in_sockets  = []
        self.in_points   = []
        self.out_sockets = []
        self.out_points  = []

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

    @property
    def right(self) -> int:
        """"""
        return self.x + self.get_width()

    @property
    def bottom(self) -> int:
        """"""
        return self.y + self.get_height()

    def intersects(self,
                   target: 'NodeFrame',
                   ) ->    'bool':
        """"""
        is_disjoint = (
            self.right  < target.x      or # left of target
            self.x      > target.right  or # right of target
            self.bottom < target.y      or # above target
            self.y      > target.bottom    # below target
        )
        return not is_disjoint

    def select(self) -> None:
        """"""
        editor = self.get_editor()

        if not editor:
            return

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

        if not canvas:
            return None

        viewport = canvas.get_parent()
        scrolled_window = viewport.get_parent()
        editor = scrolled_window.get_parent()

        return editor

from .editor import NodeEditor
from .content import NodeContent
from .socket import NodeSocket
from .socket import NodeSocketType
from .repository import NodeTemplate
