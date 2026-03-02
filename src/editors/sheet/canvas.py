# canvas.py
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

from gi.repository import Gdk
from gi.repository import Graphene
from gi.repository import Gtk

from .widgets import SheetTableFilter

class SheetCanvas(Gtk.Overlay):

    __gtype_name__ = 'SheetCanvas'

    def __init__(self) -> None:
        """"""
        super().__init__()

        self.add_css_class('sheet-canvas')

        self.renderer = SheetRenderer()

        self.connect('get-child-position', self._on_get_child_position)

    def do_snapshot(self,
                    snapshot: Gtk.Snapshot,
                    ) ->      None:
        """"""
        editor = self.get_editor()
        self.renderer.render(self,
                             snapshot,
                             self.get_width(),
                             self.get_height(),
                             editor.display,
                             editor.selection,
                             editor.document)

        bounds = Graphene.Rect().init(editor.display.left_locator_width,
                                      editor.display.top_locator_height,
                                      self.get_width(),
                                      self.get_height())
        snapshot.push_clip(bounds)

        child = self.get_first_child()
        while child:
            self.snapshot_child(child, snapshot)
            child = child.get_next_sibling()

        snapshot.pop()

    def cleanup(self) -> None:
        """"""
        self.renderer.render_cache = {}

    def _on_get_child_position(self,
                               overlay:    Gtk.Overlay,
                               widget:     Gtk.Widget,
                               allocation: Gdk.Rectangle,
                               ) ->        bool:
        """"""
        if isinstance(widget, SheetTableFilter):
            allocation.x = widget.x
            allocation.y = widget.y - 1
            allocation.width  = widget.WIDTH
            allocation.height = widget.HEIGHT
            return Gdk.EVENT_STOP
        return Gdk.EVENT_PROPAGATE

    def get_editor(self) -> 'SheetEditor':
        """"""
        overlay = self.get_parent()
        box = overlay.get_parent()
        editor = box.get_parent()
        return editor

from .editor import SheetEditor
from .renderer import SheetRenderer
