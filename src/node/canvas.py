# canvas.py
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
from gi.repository import Gsk
from gi.repository import Gtk

class NodeCanvas(Gtk.Fixed):

    __gtype_name__ = 'NodeCanvas'

    def __init__(self) -> None:
        """"""
        super().__init__()

        self._setup_controllers()

    def do_snapshot(self,
                    snapshot: Gtk.Snapshot,
                    ) ->      None:
        """"""
        editor = self.get_editor()

        self._style_manager = Adw.StyleManager.get_default()
        self._prefers_dark = self._style_manager.get_dark()

        if editor.links:
            self._draw_links(snapshot)

        child = self.get_first_child()
        while child:
            self.snapshot_child(child, snapshot)
            child = child.get_next_sibling()

        if editor.future_link:
            self._draw_future_link(snapshot)

        if editor.rubber_band:
            self._draw_rubber_band(snapshot)

    def _draw_links(self,
                    snapshot: Gtk.Snapshot,
                    ) ->      None:
        """"""
        editor = self.get_editor()

        builder_success = Gsk.PathBuilder()
        builder_warning = Gsk.PathBuilder()

        point = Graphene.Point().init(0, 0)
        radius = 6 # socket radius is always 6px

        for link in editor.links:
            *_, point_1 = link.in_socket.compute_point(self, point)
            *_, point_2 = link.out_socket.compute_point(self, point)

            point_1 = (point_1.x + radius - 2, point_1.y + radius)
            point_2 = (point_2.x + radius - 2, point_2.y + radius)

            if link.compatible:
                builder_success.move_to(*point_1)
                builder_success.line_to(*point_2)
            else:
                builder_warning.move_to(*point_1)
                builder_warning.line_to(*point_2)

        if self._prefers_dark:
            color = Gdk.RGBA(0.8706, 0.8667, 0.8549, 1.0) # equivalent to --light-3
        else:
            color = Gdk.RGBA(0.2392, 0.2196, 0.2745, 1.0) # equivalent to --dark-3

        path = builder_success.to_path()
        stroke = Gsk.Stroke(2.0)
        snapshot.append_stroke(path, stroke, color)

        if self._prefers_dark:
            color = Gdk.RGBA(0.75, 0.11, 0.16, 1.0) # equivalent to --destructive-bg-color
        else:
            color = Gdk.RGBA(0.88, 0.11, 0.14, 1.0) # equivalent to --destructive-bg-color

        path = builder_warning.to_path()
        stroke = Gsk.Stroke(3.0)
        snapshot.append_stroke(path, stroke, color)

    def _draw_future_link(self,
                          snapshot: Gtk.Snapshot,
                          ) ->      None:
        """"""
        stroke = Gsk.Stroke(3.0)

        if self._prefers_dark:
            color = Gdk.RGBA(0.8706, 0.8667, 0.8549, 1.0) # equivalent to --light-3
        else:
            color = Gdk.RGBA(0.2392, 0.2196, 0.2745, 1.0) # equivalent to --dark-3

        editor = self.get_editor()
        point_1 = editor.future_link[0]
        point_2 = editor.future_link[1]

        builder = Gsk.PathBuilder()
        builder.move_to(point_1[0], point_1[1])
        builder.line_to(point_2[0], point_2[1])

        path = builder.to_path()
        snapshot.append_stroke(path, stroke, color)

    def _draw_rubber_band(self,
                          snapshot: Gtk.Snapshot,
                          ) ->      None:
        """"""
        editor = self.get_editor()
        point_1, point_2 = editor.rubber_band

        x = point_1[0]
        y = point_1[1]
        width = point_2[0] - x
        height = point_2[1] - y

        builder = Gsk.PathBuilder()
        rect = Graphene.Rect().init(x, y, width, height)
        builder.add_rect(rect)
        path = builder.to_path()

        stroke = Gsk.Stroke(1.0)
        stroke.set_dash([4, 4])
        color = self._style_manager.get_accent_color_rgba()
        snapshot.append_stroke(path, stroke, color)

        fill_rule = Gsk.FillRule.WINDING
        color = list(color)
        color[3] = 0.15 # reduce the opacity
        color = Gdk.RGBA(*color)
        snapshot.append_fill(path, fill_rule, color)

    def _setup_controllers(self) -> None:
        """"""
        self._lclick_handler = Gtk.GestureClick(button = Gdk.BUTTON_PRIMARY)
        self._lclick_handler.set_propagation_phase(Gtk.PropagationPhase.TARGET)
        self._lclick_handler.connect('released', self._on_lmb_released)
        self.add_controller(self._lclick_handler)

        self._rclick_handler = Gtk.GestureClick(button = Gdk.BUTTON_SECONDARY)
        self._rclick_handler.set_propagation_phase(Gtk.PropagationPhase.TARGET)
        self._rclick_handler.connect('pressed', self._on_rmb_pressed)
        self.add_controller(self._rclick_handler)

        self._drag_handler = Gtk.GestureDrag()
        self._drag_handler.set_propagation_phase(Gtk.PropagationPhase.TARGET)
        self._drag_handler.connect('drag-begin', self._on_drag_begin)
        self._drag_handler.connect('drag-update', self._on_drag_update)
        self._drag_handler.connect('drag-end', self._on_drag_end)
        self.add_controller(self._drag_handler)

    def _on_lmb_released(self,
                         gesture: Gtk.GestureClick,
                         n_press: int,
                         x:       float,
                         y:       float,
                         ) ->     None:
        """"""
        editor = self.get_editor()
        editor.select_by_click()

    def _on_rmb_pressed(self,
                        gesture: Gtk.GestureClick,
                        n_press: int,
                        x:       float,
                        y:       float,
                        ) ->     None:
        """"""
        # from .context_menu import NodeContextMenu

        # popover = NodeContextMenu()
        # popover.set_parent(self)

        # rect = Gdk.Rectangle()
        # rect.x = x
        # rect.y = y
        # rect.width = 1
        # rect.height = 1
        # popover.set_pointing_to(rect)

        # popover.popup()

    def _on_drag_begin(self,
                       gesture: Gtk.GestureDrag,
                       start_x: float,
                       start_y: float,
                       ) ->     None:
        """"""
        editor = self.get_editor()
        point = (start_x, start_y)
        scalar = (point, point)
        editor.rubber_band = scalar

    def _on_drag_update(self,
                        gesture:  Gtk.GestureDrag,
                        offset_x: float,
                        offset_y: float,
                        ) ->      None:
        """"""
        editor = self.get_editor()
        point_1 = editor.rubber_band[0]
        point_2 = (point_1[0] + offset_x,
                   point_1[1] + offset_y)
        scalar = (point_1, point_2)
        editor.rubber_band = scalar
        self.queue_draw()

        # Prevent from triggering the released event.
        # We add threshold to ignore slight movement.
        if abs(offset_x) > 0.5 and abs(offset_y) > 0.5:
            self._lclick_handler.set_state(Gtk.EventSequenceState.DENIED)
            self._rclick_handler.set_state(Gtk.EventSequenceState.DENIED)

    def _on_drag_end(self,
                     gesture:  Gtk.GestureDrag,
                     offset_x: float,
                     offset_y: float,
                     ) ->      None:
        """"""
        editor = self.get_editor()
        state = gesture.get_current_event_state()
        combo = state & Gdk.ModifierType.SHIFT_MASK != 0
        editor.select_by_rubberband(combo)
        self.queue_draw()

    def get_editor(self) -> 'NodeEditor':
        """"""
        viewport = self.get_parent()
        scrolled_window = viewport.get_parent()
        editor = scrolled_window.get_parent()
        return editor

from .editor import NodeEditor
