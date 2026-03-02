# widget.py
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
from gi.repository import Gdk
from gi.repository import Graphene
from gi.repository import Gtk

class SheetTableFilter(Gtk.Widget):

    __gtype_name__ = 'SheetTableFilter'

    WIDTH  = 20
    HEIGHT = 20

    x = 0
    y = 0

    def __init__(self,
                 x:      int,
                 y:      int,
                 column: int,
                 row:    int,
                 ) ->    None:
        """"""
        super().__init__(halign = Gtk.Align.CENTER,
                         valign = Gtk.Align.CENTER)

        self.set_size_request(self.WIDTH, self.HEIGHT)

        self.x = x
        self.y = y

        self.column = column
        self.row    = row

        self._being_hovered = False

        controller = Gtk.EventControllerMotion()
        controller.connect('enter', self._on_entered)
        controller.connect('leave', self._on_left)
        self.add_controller(controller)

        self.default_cursor = Gdk.Cursor.new_from_name('default')
        self.set_cursor(self.default_cursor)

    def do_snapshot(self,
                    snapshot: Gtk.Snapshot,
                    ) ->      None:
        """"""
        style_manager = Adw.StyleManager.get_default()
        prefers_dark = style_manager.get_dark()

        x = -1
        y = +2

        bounds = Graphene.Rect().init(0, 0, self.WIDTH, self.HEIGHT)
        context = snapshot.append_cairo(bounds)

        if (
            (prefers_dark and not self._being_hovered) or
            (not prefers_dark and self._being_hovered)
        ):
            context.set_source_rgb(0.25, 0.25, 0.25)
        else:
            context.set_source_rgb(0.75, 0.75, 0.75)

        # Draw the background fill
        context.rectangle(x, y, self.WIDTH-1, self.HEIGHT-3)
        context.fill()

        if (
            (prefers_dark and not self._being_hovered) or
            (not prefers_dark and self._being_hovered)
        ):
            context.set_source_rgb(1.0, 1.0, 1.0)
        else:
            context.set_source_rgb(0.0, 0.0, 0.0)

        context.set_hairline(True)

        # Draw the left diagonal line
        start_x = x + 5
        start_y = y + 6
        end_x = x + self.WIDTH / 2
        end_y = y + self.HEIGHT - 9
        context.move_to(start_x, start_y)
        context.line_to(end_x, end_y)

        # Draw the right diagonal line
        start_x = x + self.WIDTH / 2
        start_y = y + self.HEIGHT - 9
        end_x = x + self.WIDTH - 5
        end_y = y + 6
        context.move_to(start_x, start_y)
        context.line_to(end_x, end_y)

        context.stroke()

    def _on_entered(self,
                    motion: Gtk.EventControllerMotion,
                    x:      float,
                    y:      float,
                    ) ->    None:
        """"""
        self._being_hovered = True
        self.queue_draw()

    def _on_left(self,
                 motion: Gtk.EventControllerMotion,
                 ) ->    None:
        """"""
        self._being_hovered = False
        self.queue_draw()
