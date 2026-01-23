# renderer.py
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

from cairo import Antialias
from cairo import Context
from cairo import FontOptions
from gi.repository import Adw
from gi.repository import Graphene
from gi.repository import Gtk

from .display import ChartDisplay
from .document import ChartDocument

class ChartRenderer():

    def __init__(self) -> None:
        """"""
        super().__init__()

        self.style_manager = Adw.StyleManager.get_default()

        self.prefers_dark = self.style_manager.get_dark()
        self.render_cache = {}

        self.prev_width  = 0
        self.prev_height = 0

    def render(self,
               canvas:    'ChartCanvas',
               snapshot:  'Gtk.Snapshot',
               width:     'int',
               height:    'int',
               display:   'ChartDisplay',
               document:  'ChartDocument',
               ) ->       'None':
        """"""
        bounds = Graphene.Rect().init(0, 0, width, height)
        context = snapshot.append_cairo(bounds)

        self.style_manager = Adw.StyleManager.get_default()

        self._setup_cairo_context(context)
        self._draw_placeholders(context, width, height, display, document)
        self._draw_main_contents(canvas, context, width, height, display, document)

    def _setup_cairo_context(self,
                             context: Context,
                             ) ->     None:
        """"""
        font_options = FontOptions()
        font_options.set_antialias(Antialias.GOOD)

        context.set_font_options(font_options)
        context.set_antialias(Antialias.NONE)

    def _draw_placeholders(self,
                           context:  Context,
                           width:    int,
                           height:   int,
                           display:  ChartDisplay,
                           document: ChartDocument,
                           ) ->      None:
        """"""
        if document.has_data():
            return # skip when there's data

        context.save()

        if self.prefers_dark:
            context.set_source_rgb(0.25, 0.25, 0.25)
        else:
            context.set_source_rgb(0.75, 0.75, 0.75)

        context.set_hairline(True)

        context.move_to(display.CANVAS_PADDING,
                        display.CANVAS_PADDING + display.AXIS_SIZE)
        context.line_to(width - display.CANVAS_PADDING,
                        display.CANVAS_PADDING + display.AXIS_SIZE)
        context.move_to(display.CANVAS_PADDING + display.AXIS_SIZE,
                        display.CANVAS_PADDING)
        context.line_to(display.CANVAS_PADDING + display.AXIS_SIZE,
                        height - display.CANVAS_PADDING)
        context.move_to(display.CANVAS_PADDING,
                        height - display.CANVAS_PADDING)
        context.line_to(width - display.CANVAS_PADDING,
                        height - display.CANVAS_PADDING)
        context.move_to(width - display.CANVAS_PADDING,
                        display.CANVAS_PADDING)
        context.line_to(width - display.CANVAS_PADDING,
                        height - display.CANVAS_PADDING)
        context.stroke()

        context.restore()

    def _draw_main_contents(self,
                            canvas:   'ChartCanvas',
                            context:  'Context',
                            width:    'int',
                            height:   'int',
                            display:  'ChartDisplay',
                            document: 'ChartDocument',
                            ) ->      'None':
        """"""
        if not document.has_data():
            return # skip when no data

        pass

from .canvas import ChartCanvas
