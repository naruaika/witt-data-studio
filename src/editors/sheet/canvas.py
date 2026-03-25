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
from gi.repository import Pango

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

        bounds = Graphene.Rect().init(editor.display.get_left_locator_width(),
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

    def resize_sheet_locators(self) -> None:
        """"""
        editor = self.get_editor()

        if not editor.display.show_locators:
            return

        row_index = editor.display.get_starting_row()
        max_row_number = row_index

        # Compute the last visible row number
        y = editor.display.get_top_locator_height()
        while y < self.get_height():
            max_row_number = editor.display.get_lrow_from_row(row_index)
            y += editor.display.DEFAULT_CELL_HEIGHT
            row_index += 1

        context = self.get_pango_context()
        font_desc = f'Monospace Normal Regular {editor.display.FONT_SIZE}px'
        font_desc = Pango.font_description_from_string(font_desc)

        layout = Pango.Layout.new(context)
        layout.set_text(str(max_row_number), -1)
        layout.set_font_description(font_desc)

        text_width = layout.get_size()[0] / Pango.SCALE
        cell_padding = editor.display.DEFAULT_CELL_PADDING
        locator_width = int(text_width + cell_padding * 2 + 0.5)
        locator_width = max(45, locator_width)

        if locator_width != editor.display.get_left_locator_width():
            editor.display.left_locator_width = locator_width
            self.cleanup()

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
