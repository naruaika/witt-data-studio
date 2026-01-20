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

from gi.repository import Gdk
from gi.repository import Gtk

class ChartCanvas(Gtk.Overlay):

    __gtype_name__ = 'ChartCanvas'

    def __init__(self) -> None:
        """"""
        super().__init__()

        self.add_css_class('chart-canvas')

        self.renderer = ChartRenderer()

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
                             editor.document)

        child = self.get_first_child()
        while child:
            self.snapshot_child(child, snapshot)
            child = child.get_next_sibling()

    def _on_get_child_position(self,
                               overlay:    Gtk.Overlay,
                               widget:     Gtk.Widget,
                               allocation: Gdk.Rectangle,
                               ) ->        bool:
        """"""
        return False

    def get_editor(self) -> 'ChartEditor':
        """"""
        editor = self.get_parent()
        return editor

from .editor import ChartEditor
from .renderer import ChartRenderer
