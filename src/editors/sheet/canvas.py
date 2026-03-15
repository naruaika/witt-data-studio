# canvas.py
#
# Copyright 2025 Naufan Rusyda Faikar <hello@naruaika.me>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# 	http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

from gi.repository import Gdk
from gi.repository import Graphene
from gi.repository import Gtk

from .widgets import SheetColumnDType
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
                                      0,
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
        table_widgets = (SheetColumnDType, SheetTableFilter)

        if isinstance(widget, table_widgets):
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
