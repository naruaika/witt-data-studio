# minimap.py
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

class NodeMinimap(Adw.Bin):

    __gtype_name__ = 'NodeMinimap'

    def __init__(self) -> None:
        """"""
        super().__init__()

        self._style_manager = Adw.StyleManager.get_default()

    def do_snapshot(self,
                    snapshot: Gtk.Snapshot,
                    ) ->      None:
        """"""
        editor = self.get_editor()

        scrolled_window = editor.ScrolledWindow
        vadjustment = scrolled_window.get_vadjustment()
        hadjustment = scrolled_window.get_hadjustment()

        x1 = hadjustment.get_value()
        y1 = vadjustment.get_value()
        x2 = x1 + scrolled_window.get_width()
        y2 = y1 + scrolled_window.get_height()

        # TODO: pre-compute children geometry
        canvas = editor.Canvas
        child = canvas.get_first_child()
        while child:
            x1 = min(x1, child.x)
            y1 = min(y1, child.y)
            x2 = max(x2, child.x + child.get_width())
            y2 = max(y2, child.y + child.get_height())
            child = child.get_next_sibling()

        claimed_width  = x2 - x1
        claimed_height = y2 - y1

        if claimed_width > claimed_height:
            factor = self.get_width() / claimed_width
            offset = (0, (self.get_height() - claimed_height * factor) / 2)
        else:
            factor = self.get_height() / claimed_height
            offset = ((self.get_width() - claimed_width * factor) / 2, 0)

        offset = (offset[0] - x1 * factor, offset[1] - y1 * factor)

        self._render_widgets(snapshot, factor, offset)
        self._render_viewport(snapshot, factor, offset)

    def _render_widgets(self,
                        snapshot: Gtk.Snapshot,
                        factor:   float,
                        offset:   float,
                        ) ->      None:
        """"""
        editor = self.get_editor()
        canvas = editor.Canvas

        accent_color = self._style_manager.get_accent_color_rgba()
        base_color = Gdk.RGBA(0.5, 0.5, 0.5, 1.0)
        padding = 10 # node's frame internal padding

        child = canvas.get_first_child()
        while child:
            x = (child.x + padding) * factor + offset[0]
            y = (child.y + padding) * factor + offset[1]
            width  = (child.get_width()  - padding * 2) * factor
            height = (child.get_height() - padding * 2) * factor

            bounds = Graphene.Rect().init(x, y, width, height)
            color = accent_color if child.is_selected else base_color
            snapshot.append_color(color, bounds)

            child = child.get_next_sibling()

    def _render_viewport(self,
                         snapshot: Gtk.Snapshot,
                         factor:   float,
                         offset:   float,
                         ) ->      None:
        """"""
        editor = self.get_editor()
        scrolled_window = editor.ScrolledWindow
        vadjustment = scrolled_window.get_vadjustment()
        hadjustment = scrolled_window.get_hadjustment()

        x = hadjustment.get_value() * factor + offset[0]
        y = vadjustment.get_value() * factor + offset[1]
        width  = scrolled_window.get_width()  * factor
        height = scrolled_window.get_height() * factor

        builder = Gsk.PathBuilder()
        rect = Graphene.Rect().init(x, y, width, height)
        builder.add_rect(rect)
        path = builder.to_path()

        stroke = Gsk.Stroke(1.0)
        color = Gdk.RGBA(0.5, 0.5, 0.5, 1.0)
        snapshot.append_stroke(path, stroke, color)

        fill_rule = Gsk.FillRule.WINDING
        color = list(color)
        color[3] = 0.15 # reduce the opacity
        color = Gdk.RGBA(*color)
        snapshot.append_fill(path, fill_rule, color)

    def get_editor(self) -> 'NodeEditor':
        """"""
        editor = self.get_parent()
        return editor

from .editor import NodeEditor
