# time_picker.py
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
from gi.repository import GObject
from gi.repository import Graphene
from gi.repository import Gsk
from gi.repository import Gtk
import math

class TimePicker(Gtk.Box):

    __gtype_name__ = 'TimePicker'

    __gsignals__ = {
        'time-updated': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    CLOCK_SIZE = 300

    MODE_HOUR   = 0
    MODE_MINUTE = 1
    MODE_SECOND = 2

    def __init__(self,
                 *args:    list,
                 **kwargs: dict,
                 ) ->      None:
        """"""
        super().__init__(*args, **kwargs)

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(10)
        self.add_css_class('time-picker')

        self._style_manager = Adw.StyleManager.get_default()

        self.hour   = 0
        self.minute = 0
        self.second = 0

        self.mode = self.MODE_HOUR

        self._labels = []

        self._build_clock()
        self._build_mode_switch()

    def get_hour(self) -> int:
        """"""
        return self.hour

    def set_hour(self,
                 value: int,
                 ) ->   None:
        """"""
        self.hour = value
        self.queue_draw()

    def get_minute(self) -> int:
        """"""
        return self.minute

    def set_minute(self,
                   value: int,
                   ) ->   None:
        """"""
        self.minute = value
        self.queue_draw()

    def get_second(self) -> int:
        """"""
        return self.second

    def set_second(self,
                   value: int,
                   ) ->   None:
        """"""
        self.second = value
        self.queue_draw()

    def set_mode(self,
                 mode: int,
                 ) ->  None:
        """"""
        self.mode = mode

        match self.mode:
            case self.MODE_HOUR:
                self._build_hour_labels()
                self.button_hour.set_active(True)
            case self.MODE_MINUTE:
                self._build_minute_labels()
                self.button_minute.set_active(True)
            case self.MODE_SECOND:
                self._build_second_labels()
                self.button_second.set_active(True)

        self.queue_draw()

    def _get_active_value(self) -> int:
        """"""
        match self.mode:
            case self.MODE_HOUR:
                return self.hour
            case self.MODE_MINUTE:
                return self.minute
            case self.MODE_SECOND:
                return self.second

    def _set_active_value(self,
                          value: int,
                          ) ->   None:
        """"""
        match self.mode:
            case self.MODE_HOUR:
                self.hour = value
            case self.MODE_MINUTE:
                self.minute = value
            case self.MODE_SECOND:
                self.second = value
        self.queue_draw()

    def _build_clock(self) -> None:
        """"""
        self.clock = Gtk.Fixed()
        self.clock.set_size_request(self.CLOCK_SIZE, self.CLOCK_SIZE)

        radius = self.CLOCK_SIZE / 2 - 18

        self._oradius = radius - 18
        self._iradius = radius - 54

        self._build_hour_labels()

        self.append(self.clock)

        controller = Gtk.GestureDrag()
        controller.connect('drag-begin', self._on_drag_begin)
        controller.connect('drag-update', self._on_drag_update)
        controller.connect('drag-end', self._on_drag_end)
        self.clock.add_controller(controller)

    def _build_mode_switch(self) -> None:
        """"""
        box = Gtk.Box(orientation   = Gtk.Orientation.HORIZONTAL,
                      halign        = Gtk.Align.CENTER,
                      spacing       = 6,
                      margin_bottom = 18)

        self.button_hour   = Gtk.ToggleButton(label = 'H')
        self.button_minute = Gtk.ToggleButton(label = 'M')
        self.button_second = Gtk.ToggleButton(label = 'S')

        self.button_minute.set_group(self.button_hour)
        self.button_second.set_group(self.button_hour)

        for button, mode in [
            (self.button_hour,   self.MODE_HOUR),
            (self.button_minute, self.MODE_MINUTE),
            (self.button_second, self.MODE_SECOND),
        ]:
            button.add_css_class('circular')
            button.connect('toggled', self._on_mode_toggled, mode)
            box.append(button)

        self.button_hour.set_active(True)

        self.append(box)

    def _on_mode_toggled(self,
                         button: Gtk.ToggleButton,
                         mode:   int = -1,
                         ) ->    None:
        """"""
        if not button.get_active():
            return
        if mode == -1:
            return
        self.set_mode(mode)

    def _place_label(self,
                     text:      str,
                     index:     int,
                     divisions: int,
                     radius:    float,
                     visible:   bool = True,
                     ) ->       None:
        """"""
        cx = self.CLOCK_SIZE / 2
        cy = self.CLOCK_SIZE / 2

        angle = index / divisions * 2 * math.pi - math.pi / 2

        x = cx + math.cos(angle) * radius - 18
        y = cy + math.sin(angle) * radius - 18

        label = Gtk.Label(label      = text,
                          halign     = Gtk.Align.CENTER,
                          valign     = Gtk.Align.CENTER,
                          opacity    = 1 if visible else 0,
                          can_target = 1 if visible else 0)
        label.set_size_request(36, 36)

        self.clock.put(label, x, y)
        self._labels.append(label)

    def _clear_labels(self) -> None:
        """"""
        for label in self._labels:
            self.clock.remove(label)
        self._labels.clear()

    def _build_hour_labels(self) -> None:
        """"""
        self._clear_labels()

        for hour in range(24):
            if 1 <= hour <= 12:
                radius = self._oradius
            else:
                radius = self._iradius

            index = hour % 12
            if hour == 0:
                index = 12
            if hour == 12:
                index = 0

            self._place_label(str(hour), index, 12, radius)

    def _build_minute_labels(self) -> None:
        """"""
        self._clear_labels()

        for minute in range(60):
            visible = minute % 5 == 0
            self._place_label(str(minute), minute, 60, self._oradius, visible)

    def _build_second_labels(self) -> None:
        """"""
        self._clear_labels()

        for second in range(60):
            visible = second % 5 == 0
            self._place_label(str(second), second, 60, self._oradius, visible)

    def _on_drag_begin(self,
                       gesture: Gtk.GestureDrag,
                       start_x: float,
                       start_y: float,
                       ) ->     None:
        """"""
        self._on_drag_update(gesture, 0, 0)

    def _on_drag_update(self,
                        gesture:  Gtk.GestureDrag,
                        offset_x: float,
                        offset_y: float,
                        ) ->      None:
        """"""
        success, x, y = gesture.get_point()

        if not success:
            return

        value = self._get_value_from_position(x, y)

        if value != self._get_active_value():
            self._set_active_value(value)

    def _on_drag_end(self,
                     gesture:  Gtk.GestureDrag,
                     offset_x: float,
                     offset_y: float,
                     ) ->      None:
        """"""
        self._on_drag_update(gesture, 0, 0)

        match self.mode:
            case self.MODE_HOUR:
                self.set_mode(self.MODE_MINUTE)
            case self.MODE_MINUTE:
                self.set_mode(self.MODE_SECOND)
            case self.MODE_SECOND:
                self.set_mode(self.MODE_HOUR)

        self.emit('time-updated')

    def _get_value_from_position(self,
                                 x:   int,
                                 y:   int,
                                 ) -> int:
        """"""
        cx = self.CLOCK_SIZE / 2
        cy = self.CLOCK_SIZE / 2

        dx = x - cx
        dy = y - cy

        angle = math.atan2(dy, dx) + math.pi / 2
        if angle < 0:
            angle += 2 * math.pi

        if self.mode == self.MODE_HOUR:
            distance = math.hypot(dx, dy)
            index = int(round((angle / (2 * math.pi)) * 12)) % 12
            is_outer = abs(distance - self._oradius) < abs(distance - self._iradius)
            if is_outer:
                if index == 0:
                    return 12
                return index
            if index == 0:
                return 0
            return index + 12

        else:
            return int(round((angle / (2 * math.pi)) * 60)) % 60

    def do_snapshot(self,
                    snapshot: Gtk.Snapshot,
                    ) ->      None:
        """"""
        accent_color = self._style_manager.get_accent_color_rgba()
        prefers_dark = self._style_manager.get_dark()

        cx = self.CLOCK_SIZE / 2
        cy = self.CLOCK_SIZE / 2

        self._draw_background(snapshot, prefers_dark, cx, cy)

        Gtk.Fixed.do_snapshot(self, snapshot)

        self._draw_center_dot(snapshot, accent_color, cx, cy)

        value = self._get_active_value()

        if self.mode == self.MODE_HOUR:
            if 1 <= value <= 12:
                radius = self._oradius
            else:
                radius = self._iradius
            divisions = 12
        else:
            radius = self._oradius
            divisions = 60

        angle = (value % divisions) / divisions * 2 * math.pi - math.pi / 2

        x2 = cx + math.cos(angle) * radius
        y2 = cy + math.sin(angle) * radius

        self._draw_hand_line(snapshot, accent_color, cx, cy, x2, y2)

        self._draw_hand_head(snapshot, accent_color, x2, y2)

        self._draw_head_text(snapshot, x2, y2)

    def _draw_background(self,
                         snapshot:     Gtk.Snapshot,
                         prefers_dark: bool,
                         cx:           float,
                         cy:           float,
                         ) ->          None:
        """"""
        radius = self.CLOCK_SIZE / 2 - 18
        builder = Gsk.PathBuilder()
        center = Graphene.Point().init(cx, cy)
        builder.add_circle(center, radius)
        path = builder.to_path()
        if prefers_dark:
            color = Gdk.RGBA(0.25, 0.25, 0.27, 1.0)
        else:
            color = Gdk.RGBA(0.96, 0.96, 0.96, 1.0)
        snapshot.append_fill(path, Gsk.FillRule.WINDING, color)

    def _draw_center_dot(self,
                         snapshot:     Gtk.Snapshot,
                         accent_color: Gdk.RGBA,
                         cx:           float,
                         cy:           float,
                         ) ->          None:
        """"""
        builder = Gsk.PathBuilder()
        center = Graphene.Point().init(cx, cy)
        builder.add_circle(center, 6)
        path = builder.to_path()
        snapshot.append_fill(path, Gsk.FillRule.WINDING, accent_color)

    def _draw_hand_line(self,
                        snapshot:     Gtk.Snapshot,
                        accent_color: Gdk.RGBA,
                        cx:           float,
                        cy:           float,
                        x2:           float,
                        y2:           float,
                        ) ->          None:
        """"""
        builder = Gsk.PathBuilder()
        builder.move_to(cx, cy)
        builder.line_to(x2, y2)
        path = builder.to_path()
        stroke = Gsk.Stroke.new(2)
        stroke.set_line_cap(Gsk.LineCap.ROUND)
        snapshot.append_stroke(path, stroke, accent_color)

    def _draw_hand_head(self,
                        snapshot:     Gtk.Snapshot,
                        accent_color: Gdk.RGBA,
                        x2:           float,
                        y2:           float,
                        ) ->          None:
        """"""
        builder = Gsk.PathBuilder()
        center = Graphene.Point().init(x2, y2)
        builder.add_circle(center, 18)
        path = builder.to_path()
        snapshot.append_fill(path, Gsk.FillRule.WINDING, accent_color)

    def _draw_head_text(self,
                        snapshot: Gtk.Snapshot,
                        x2:       float,
                        y2:       float,
                        ) ->      None:
        """"""
        value = self._get_active_value()
        layout = self.create_pango_layout(str(value))
        _, rect = layout.get_pixel_extents()
        tx = x2 - rect.width  / 2
        ty = y2 - rect.height / 2
        snapshot.translate(Graphene.Point().init(tx, ty))
        snapshot.append_layout(layout, Gdk.RGBA(1, 1, 1, 1))
