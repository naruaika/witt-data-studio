# view.py
#
# Copyright (c) 2025 Naufan Rusyda Faikar <hello@naruaika.me>
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

from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gtk

from .canvas import ChartCanvas
from .display import ChartDisplay
from .document import ChartDocument

class ChartView():

    def __init__(self,
                 Canvas:              ChartCanvas,
                 HorizontalScrollbar: Gtk.Scrollbar,
                 VerticalScrollbar:   Gtk.Scrollbar,
                 document:            ChartDocument,
                 display:             ChartDisplay,
                 ) ->                 None:
        """"""
        self.Canvas              = Canvas
        self.HorizontalScrollbar = HorizontalScrollbar
        self.VerticalScrollbar   = VerticalScrollbar

        self.document = document
        self.display  = display

        self.is_refreshing_ui  = False
        self.is_panning_canvas = False

        self._setup_canvas()
        self._setup_scrollbars()

    def _setup_canvas(self) -> None:
        """"""
        # Define scroll behaviour on the main canvas
        controller = Gtk.EventControllerScroll()
        controller.set_flags(Gtk.EventControllerScrollFlags.BOTH_AXES)
        controller.connect('scroll', self._on_canvas_scrolled)
        self.Canvas.add_controller(controller)

        # Define clicking behaviour on the main canvas
        controller = Gtk.GestureClick()
        controller.connect('pressed', self._on_canvas_lmb_pressed)
        self.Canvas.add_controller(controller)

        # Define leaving behaviour the main canvas
        controller = Gtk.EventControllerFocus()
        controller.connect('leave', self._on_canvas_unfocused)
        self.Canvas.add_controller(controller)

        # Define key-pressing behaviour on the main canvas
        controller = Gtk.EventControllerKey()
        controller.connect('key-pressed', self._on_canvas_key_pressed)
        self.Canvas.add_controller(controller)

    def _on_canvas_scrolled(self,
                            event: Gtk.EventControllerScroll,
                            dx:    float,
                            dy:    float,
                            ) ->   bool:
        """"""
        scroll_unit = event.get_unit()
        event_state = event.get_current_event_state()

        # Change direction of scroll based on shift key
        if scroll_unit == Gdk.ScrollUnit.WHEEL:
            if event_state & Gdk.ModifierType.SHIFT_MASK == 0:
                pass
            elif dy < 0 or 0 < dy:
                dx, dy = dy, 0
            elif dx < 0 or 0 < dx:
                dy, dx = dx, 0

        # Convert to scroll unit (in pixels)
        dy = int(dy * self.display.scroll_increment)
        dx = int(dx * self.display.scroll_increment)

        # Make panning experience with touchpad more friendly
        if scroll_unit == Gdk.ScrollUnit.SURFACE:
            dy *= self.display.pan_increment
            dx *= self.display.pan_increment

        self.is_panning_canvas = True
        self.is_refreshing_ui = True

        vadjustment = self.VerticalScrollbar.get_adjustment()
        hadjustment = self.HorizontalScrollbar.get_adjustment()

        scroll_y_position = vadjustment.get_value()
        scroll_x_position = hadjustment.get_value()

        scroll_y_upper = max(0, scroll_y_position + dy + self.Canvas.get_height())
        scroll_x_upper = max(0, scroll_x_position + dx + self.Canvas.get_width())

        vadjustment.set_upper(scroll_y_upper)
        hadjustment.set_upper(scroll_x_upper)

        scroll_y_position = max(0, scroll_y_position + dy)
        scroll_x_position = max(0, scroll_x_position + dx)

        vadjustment.set_value(scroll_y_position)
        hadjustment.set_value(scroll_x_position)

        self.is_refreshing_ui = False

        self.update_by_scroll()

        self.Canvas.queue_draw()

        return True

    def _on_canvas_lmb_pressed(self,
                               event:   Gtk.GestureClick,
                               n_press: int,
                               x:       float,
                               y:       float,
                               ) ->     None:
        """"""
        widget = event.get_widget()

        widget.set_focusable(True)
        widget.grab_focus()

    def _on_canvas_unfocused(self,
                             event: Gtk.EventControllerFocus,
                             ) ->   None:
        """"""
        self.Canvas.set_focusable(False)

    def _on_canvas_key_pressed(self,
                               event:   Gtk.EventControllerKey,
                               keyval:  int,
                               keycode: int,
                               state:   Gdk.ModifierType,
                               ) ->     bool:
        """"""
        # Prevent from interrupting any window-level actions
        if (
            state in {
                Gdk.ModifierType.CONTROL_MASK,
                Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK,
            }
            and keyval in {
                Gdk.KEY_Tab,
                Gdk.KEY_ISO_Left_Tab,
            }
        ):
            return Gdk.EVENT_PROPAGATE

        if keyval in {
            Gdk.KEY_Tab,
            Gdk.KEY_ISO_Left_Tab,
            Gdk.KEY_Return,
            Gdk.KEY_Left,
            Gdk.KEY_Right,
            Gdk.KEY_Up,
            Gdk.KEY_Down,
        }:
            return Gdk.EVENT_STOP

        if keyval == Gdk.KEY_Delete:
            return Gdk.EVENT_STOP

        if keyval == Gdk.KEY_Menu:
            return Gdk.EVENT_STOP

        return Gdk.EVENT_PROPAGATE

    def _setup_scrollbars(self) -> None:
        """"""
        scroll_increment = self.display.scroll_increment
        page_increment = self.display.page_increment

        # Watch vertical scroll position
        vadjustment = Gtk.Adjustment.new(0, 0, 1, scroll_increment, page_increment, 0)
        vadjustment.connect('value-changed', self._on_scrollbar_changed)
        self.VerticalScrollbar.set_adjustment(vadjustment)

        # Watch horizontal scroll position
        hadjustment = Gtk.Adjustment.new(0, 0, 1, scroll_increment, page_increment, 0)
        hadjustment.connect('value-changed', self._on_scrollbar_changed)
        self.HorizontalScrollbar.set_adjustment(hadjustment)

        # Set custom behaviour for the horizontal scroll bar
        controller = Gtk.EventControllerMotion()
        controller.connect('enter', self._on_scrollbar_entered)
        controller.connect('leave', self._on_scrollbar_left)
        self.HorizontalScrollbar.add_controller(controller)

        # Set custom behaviour for the vertical scroll bar
        controller = Gtk.EventControllerMotion()
        controller.connect('enter', self._on_scrollbar_entered)
        controller.connect('leave', self._on_scrollbar_left)
        self.VerticalScrollbar.add_controller(controller)

        def do_setup() -> bool:
            """"""
            window = self.Canvas.get_root()
            if not window:
                return Gdk.EVENT_STOP
            tab_view = window.TabView
            canvas_width = tab_view.get_width()
            canvas_height = tab_view.get_height()
            if canvas_width and canvas_height:
                vadjustment = self.VerticalScrollbar.get_adjustment()
                hadjustment = self.HorizontalScrollbar.get_adjustment()
                vadjustment.set_page_size(canvas_height)
                hadjustment.set_page_size(canvas_width)
                return Gdk.EVENT_PROPAGATE
            return Gdk.EVENT_STOP

        GLib.idle_add(do_setup)

    def _on_scrollbar_changed(self,
                              source: GObject.Object,
                              ) ->    None:
        """"""
        self.update_by_scroll()

    def _on_scrollbar_entered(self,
                              motion: Gtk.EventControllerMotion,
                              x:      float,
                              y:      float,
                              ) ->    None:
        """"""
        scrollbar = motion.get_widget()
        scrollbar.add_css_class('hovering')

    def _on_scrollbar_left(self,
                           motion: Gtk.EventControllerMotion,
                           ) ->    None:
        """"""
        scrollbar = motion.get_widget()
        scrollbar.remove_css_class('hovering')

    def update_by_scroll(self) -> None:
        """"""
        if self.is_refreshing_ui:
            return

        vadjustment = self.VerticalScrollbar.get_adjustment()
        hadjustment = self.HorizontalScrollbar.get_adjustment()

        scroll_y_position = int(vadjustment.get_value())
        scroll_x_position = int(hadjustment.get_value())

        content_height = self.Canvas.get_height()
        content_width = self.Canvas.get_width()

        new_y_upper = max(content_height, scroll_y_position + self.Canvas.get_height())
        new_x_upper = max(content_width, scroll_x_position + self.Canvas.get_width())

        vadjustment.set_upper(new_y_upper)
        hadjustment.set_upper(new_x_upper)

        vadjustment.set_page_size(self.Canvas.get_height())
        hadjustment.set_page_size(self.Canvas.get_width())

        self.display.scroll_y_position = scroll_y_position
        self.display.scroll_x_position = scroll_x_position

        self.is_panning_canvas = False

    def update_scrollbar(self,
                         x:   int,
                         y:   int,
                         ) -> None:
        """"""
        self.is_refreshing_ui = True

        vadjustment = self.VerticalScrollbar.get_adjustment()
        hadjustment = self.HorizontalScrollbar.get_adjustment()

        scroll_y_upper = vadjustment.get_upper()
        scroll_x_upper = hadjustment.get_upper()

        scroll_y_upper = max(scroll_y_upper, y + self.Canvas.get_height())
        scroll_x_upper = max(scroll_x_upper, x + self.Canvas.get_width())

        vadjustment.set_upper(scroll_y_upper)
        hadjustment.set_upper(scroll_x_upper)

        vadjustment.set_value(y)
        hadjustment.set_value(x)

        self.is_refreshing_ui = False
