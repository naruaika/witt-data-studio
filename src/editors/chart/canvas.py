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

from .editor   import ChartEditor
from .renderer import ChartRenderer
