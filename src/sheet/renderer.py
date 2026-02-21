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
from cairo import FORMAT_ARGB32
from cairo import ImageSurface
from datetime import datetime
from datetime import date
from datetime import time
from datetime import timedelta
from decimal import Decimal
from gi.repository import Adw
from gi.repository import Graphene
from gi.repository import Gtk
from gi.repository import Pango
from gi.repository import PangoCairo
import re

from ..core.utils import print_timedelta

from .document import SheetDocument
from .display import SheetDisplay
from .selection import SheetSelection

WHITESPACE_PATTERN = re.compile(r'(^\s+)|(\s+$)', re.MULTILINE)

class SheetRenderer():

    def __init__(self) -> None:
        """"""
        super().__init__()

        self.style_manager = Adw.StyleManager.get_default()

        self.prefers_dark = self.style_manager.get_dark()
        self.render_cache = {}

        self._prev_width  = 0
        self._prev_height = 0

    def render(self,
               canvas:    'SheetCanvas',
               snapshot:  'Gtk.Snapshot',
               width:     'int',
               height:    'int',
               display:   'SheetDisplay',
               selection: 'SheetSelection',
               document:  'SheetDocument',
               ) ->       'None':
        """"""
        # I don't want to use Cairo but there's no choice; my current algorithm using Cairo
        # is superior compared to my new algorithm using GSK with OpenGL (sadly not Vulkan).
        bounds = Graphene.Rect().init(0, 0, width, height)
        context = snapshot.append_cairo(bounds)

        self.style_manager = Adw.StyleManager.get_default()

        # We may not want to change the order of these calls for any reasons :)
        self._check_render_caches(width, height, selection)
        self._setup_cairo_context(context)
        self._draw_headers_backgrounds(context, width, height, display)
        self._draw_selection_backgrounds(context, width, height, display, selection)
        self._draw_headers_contents(canvas, context, width, height, display)
        self._draw_cells_contents(canvas, context, width, height, display, document)
        self._draw_cells_borders(context, width, height, display)
        self._draw_selection_borders(context, width, height, display, selection)

    def _check_render_caches(self,
                             new_width:  'int',
                             new_height: 'int',
                             selection:  'SheetSelection',
                             ) ->        'None':
        """"""
        prefers_dark = self.style_manager.get_dark()
        if prefers_dark != self.prefers_dark:
            self.prefers_dark = prefers_dark
            self.render_cache = {}

        self.color_accent = self.style_manager.get_accent_color_rgba()

        if (
            self._prev_width  == new_width and
            self._prev_height == new_height
        ):
            return

        active = selection.current_active_range

        # Adjust the selection sizes
        if active.ctype == 'corner':
            active.width = new_width
            active.height = new_height
        if active.ctype == 'top':
            active.height = new_height
        if active.ctype == 'left':
            active.width = new_width

        # Invalidate some parts of the cached render area
        if 'content' in self.render_cache:
            cached_content = self.render_cache['content']
            cached_height = cached_content['height']
            cached_width = cached_content['width']
            new_area_bigger_than_cached = new_height > cached_height or \
                                          new_width  > cached_width

            if new_area_bigger_than_cached:
                x_offset = new_width  - self._prev_width
                y_offset = new_height - self._prev_height

                if x_offset != 0:
                    self.render_cache['content']['x_pos']  -= x_offset
                    self.render_cache['content']['x_trans'] = x_offset

                if y_offset != 0:
                    self.render_cache['content']['y_pos']  -= y_offset
                    self.render_cache['content']['y_trans'] = y_offset

        self._prev_width  = new_width
        self._prev_height = new_height

    def _setup_cairo_context(self,
                             context: Context,
                             ) ->     None:
        """"""
        # I don't actually see any difference between the default and good antialiasing,
        # but I'll leave it here for now
        font_options = FontOptions()
        font_options.set_antialias(Antialias.GOOD)

        # I assume this is mandatory for drawing hairline type lines,
        # I might be don't remember correctly though :/
        context.set_font_options(font_options)
        context.set_antialias(Antialias.NONE)

    def _draw_headers_backgrounds(self,
                                  context: Context,
                                  width:   int,
                                  height:  int,
                                  display: SheetDisplay,
                                  ) ->     None:
        """"""
        context.save()

        # The only reason is because we want to separate the headers from the contents.
        # I do agree that it's not always good to hardcode like this, so let's flag it
        # as a TODO for now.
        if self.prefers_dark:
            context.set_source_rgb(0.13, 0.13, 0.15)
        else:
            context.set_source_rgb(1.00, 1.00, 1.00)

        context.rectangle(0,
                          0,
                          width,
                          display.top_locator_height)
        context.rectangle(0,
                          display.top_locator_height,
                          display.left_locator_width,
                          height)
        context.fill()

        context.restore()

    def _draw_selection_backgrounds(self,
                                    context:   Context,
                                    width:     int,
                                    height:    int,
                                    display:   SheetDisplay,
                                    selection: SheetSelection,
                                    ) ->       None:
        """"""
        context.save()

        # range_x and range_y were adjusted by the sheet document, so now they are relative to the top
        # of the viewport, meaning they'll be negative if the user scrolled down. The calculations below
        # is only for optimization purposes or to handle the case where the selection size is too big so
        # that it can only be partially drawn.
        arange = selection.current_active_range
        range_x, range_y, range_width, range_height = self._get_selection_range(arange.x,
                                                                                arange.y,
                                                                                arange.width,
                                                                                arange.height,
                                                                                width,
                                                                                height,
                                                                                display,
                                                                                auto_offset = False)

        # Clipping for when the user selects the entire row(s). You may notice that
        # I didn't adjust the width and height as it's not worth the complexity.
        if arange.column == 0:
            context.rectangle(-1,
                              display.top_locator_height - 1,
                              width,
                              height)
            context.clip()
        # Clipping for when the user selects the entire column(s)
        if arange.row == 0:
            context.rectangle(display.left_locator_width - 1,
                              -1,
                              width,
                              height)
            context.clip()
        # Clipping for general use cases
        if arange.column > 0 and arange.row > 0:
            context.rectangle(display.left_locator_width - 1,
                              display.top_locator_height - 1,
                              width,
                              height)
            context.clip()

        # Reduces the opacity of the accent color so that it doesn't look too bright,
        # we try to imitate the behavior of other applications.
        accent_rgba = list(self.color_accent)
        accent_rgba[3] = 0.2
        context.set_source_rgba(*accent_rgba)

        # Draw the selection only if it's perceivable
        if range_width > 0 and range_height > 0:
            context.rectangle(range_x,
                              range_y,
                              range_width,
                              range_height)
            context.fill()

        # Indicates that the user has selected the entire column(s) by highlighting all the row headers
        if arange.column > 0 and arange.row == 0:
            context.reset_clip()
            context.rectangle(0,
                              display.top_locator_height,
                              display.left_locator_width,
                              height)
            context.fill()

        # Indicates that the user has selected the entire row(s) by highlighting all the column headers
        if arange.column == 0 and arange.row > 0:
            context.reset_clip()
            context.rectangle(display.left_locator_width,
                              0,
                              width,
                              display.top_locator_height)
            context.fill()

        # Indicates that the user has a selection by highlighting the row and column header(s)
        if arange.column > 0 and arange.row > 0:
            context.reset_clip()
            context.rectangle(display.left_locator_width - 1,
                              0,
                              width,
                              height)
            context.clip()
            context.rectangle(range_x,
                              0,
                              range_width,
                              display.top_locator_height)
            context.fill()

            context.reset_clip()
            context.rectangle(0,
                              display.top_locator_height - 1,
                              width,
                              height)
            context.clip()
            context.rectangle(0,
                              range_y,
                              display.left_locator_width,
                              range_height)
            context.fill()

        # We want more emphasis for when the user has selected column(s), row(s), or even the entire sheet,
        # so we'll increase the opacity again
        accent_rgba[3] = 1.0
        context.set_source_rgba(*accent_rgba)

        # Bold highlight all the headers if the user has selected the entire sheet
        if arange.column == 0 and arange.row == 0:
            context.reset_clip()
            context.rectangle(display.left_locator_width,
                              range_y,
                              width,
                              display.top_locator_height)
            context.rectangle(range_x,
                              display.top_locator_height,
                              display.left_locator_width,
                              range_height)
            context.rectangle(0,
                              0,
                              display.left_locator_width,
                              display.top_locator_height)
            context.fill()

        # Bold highlight the selected column(s) header
        if arange.column > 0 and arange.row == 0:
            context.reset_clip()
            context.rectangle(display.left_locator_width - 1,
                              -1,
                              width,
                              height)
            context.clip()
            context.rectangle(range_x,
                              range_y,
                              range_width,
                              display.top_locator_height)
            context.fill()

        # Bold highlight the selected row(s) header
        if arange.column == 0 and arange.row > 0:
            context.reset_clip()
            context.rectangle(-1,
                              display.top_locator_height - 1,
                              width,
                              height)
            context.clip()
            context.rectangle(range_x,
                              range_y,
                              display.left_locator_width,
                              range_height)
            context.fill()

        # It's important to differentiate between the active cell and the selection range
        # because the active cell is the only one that its data is appearing in the input bar.
        # Here we reset the color of the drawing context back to the canvas background color.
        if self.prefers_dark:
            context.set_source_rgb(0.13, 0.13, 0.15)
        else:
            context.set_source_rgb(0.98, 0.98, 0.98)

        cell = selection.current_active_cell

        context.reset_clip()
        context.rectangle(display.left_locator_width - 1,
                          display.top_locator_height - 1,
                          width,
                          height)
        context.clip()
        context.rectangle(cell.x,
                          cell.y,
                          cell.width,
                          cell.height)
        context.fill()

        context.restore()

    def _draw_headers_contents(self,
                               canvas:  'SheetCanvas',
                               context: 'Context',
                               width:   'int',
                               height:  'int',
                               display: 'SheetDisplay',
                               ) ->     'None':
        """"""
        context.save()

        # Monospace is the best in my opinion for the headers, especially when it comes to the row headers
        # which are numbers so that it can be easier to read because of the good visual alignment.
        head_font_desc = f'Monospace Normal Bold {display.FONT_SIZE}px #tnum=1'
        head_font_desc = Pango.font_description_from_string(head_font_desc)

        # Use system default font family for drawing text
        font_desc = canvas.get_pango_context().get_font_description()
        font_family = font_desc.get_family() if font_desc else 'Sans'
        body_font_desc = f'{font_family} Normal Bold {display.FONT_SIZE}px #tnum=1'
        body_font_desc = Pango.font_description_from_string(body_font_desc)

        layout = PangoCairo.create_layout(context)
        layout.set_font_description(head_font_desc)

        # We should achieve the high contrast between the text and the canvas background, though I'm aware
        # of the potential problems with using the pure black and white colors. Let's decide that later.
        text_color = (0.0, 0.0, 0.0)
        if self.prefers_dark:
            text_color = (1.0, 1.0, 1.0)
        context.set_source_rgb(*text_color)

        context.save()
        context.rectangle(display.left_locator_width,
                          0,
                          width,
                          height)
        context.clip()

        # Draw column headers texts (centered)
        # It's so rare to see a worksheet go beyond Z*9 columns, but it's better to be prepared for it
        # anyway by having defining the clip region to prevent the text from overflowing to the next cells.
        col_index = display.get_starting_column()
        x = display.get_cell_x_from_column(col_index)

        while x < width:
            lcol_index = display.get_lcolumn_from_column(col_index)
            cell_width = display.get_cell_width_from_column(col_index)

            cell_text = display.get_column_name_from_column(lcol_index)
#           layout.set_font_description(head_font_desc)
            layout.set_text(cell_text, -1)

            text_width = layout.get_pixel_size()[0]
            x_text = x + (cell_width - text_width) / 2

            context.save()
            context.rectangle(x,
                              0,
                              cell_width - 2,
                              display.top_locator_height)
            context.clip()

            context.move_to(x_text, 2)
            PangoCairo.show_layout(context, layout)

            context.restore()

            x += cell_width
            col_index += 1

        context.restore()

#       layout.set_font_description(head_font_desc)

        context.save()
        context.rectangle(0,
                          display.top_locator_height,
                          width,
                          height)
        context.clip()

        # Draw row headers texts (right-aligned)
        row_index = display.get_starting_row()
        y = display.get_cell_y_from_row(row_index)

        while y < height:
            cell_text = display.get_lrow_from_row(row_index)
            layout.set_text(str(cell_text), -1)
            text_width = layout.get_pixel_size()[0]
            x = display.left_locator_width - text_width - display.DEFAULT_CELL_PADDING

            context.move_to(x, 2 + y)
            PangoCairo.show_layout(context, layout)

            y += display.get_cell_height_from_row(row_index)
            row_index += 1

        context.restore()

    def _draw_cells_contents(self,
                             canvas:   'SheetCanvas',
                             context:  'Context',
                             width:    'int',
                             height:   'int',
                             display:  'SheetDisplay',
                             document: 'SheetDocument',
                             ) ->      'None':
        """"""
        if not document.has_data():
            return # skip when no data

        # Drawing loop boundaries
        x_start = display.left_locator_width
        y_start = display.top_locator_height
        x_end = width
        y_end = height

        # Boundaries for non-cached area
        nx_start = x_start
        ny_start = y_start
        nx_end = x_end
        ny_end = y_end

        use_cache = True

        # Create the cache if it doesn't exist
        if 'content' not in self.render_cache:
            self.render_cache['content'] = {
                'surface': ImageSurface(FORMAT_ARGB32, width, height),
                'width':   width,
                'height':  height,
                'x_pos':   display.scroll_x_position,
                'y_pos':   display.scroll_y_position,
                'x_trans': 0,
                'y_trans': 0,
            }
            use_cache = False

        rcache = self.render_cache['content']
        ccontext = Context(rcache['surface'])

        if use_cache:
            # Calculate the scroll position offset
            x_offset = display.scroll_x_position - rcache['x_pos']
            y_offset = display.scroll_y_position - rcache['y_pos']

            # Prevent the canvas from being re-drawn when the scroll isn't changed
            if x_offset == 0 and y_offset == 0:
                context.set_source_surface(rcache['surface'], 0, 0)
                context.paint()
                return

            nsurface = ImageSurface(FORMAT_ARGB32, width, height)
            ncontext = Context(nsurface)

            # Reinitialize the top and left area boundaries
            col_index = display.get_starting_column()
            row_index = display.get_starting_row()
            nx_start = display.get_cell_x_from_column(col_index)
            ny_start = display.get_cell_y_from_row(row_index)

            # Use cache if only the cache area will be visible in the viewport
            # and the canvas movement is not diagonal.
            if (
                abs(y_offset) < height and
                abs(x_offset) < width
            ):
                # When the user scrolls the canvas to the right
                if x_offset > 0:
                    nx_start = display.get_cell_x_from_point(width - x_offset)
                    cwidth = nx_start - x_start
                    ncontext.rectangle(x_start, y_start, cwidth, y_end)
                    ncontext.clip()
                # When the user scrolls the canvas to the left
                if x_offset < 0:
                    nx_end = display.get_cell_x_from_point(x_start - x_offset)
                    cwidth = display.get_cell_width_from_point(x_start - x_offset)
                    ncontext.rectangle(nx_end + cwidth, y_start, x_end, y_end)
                    ncontext.clip()
                # When the user scrolls the canvas down
                if y_offset > 0:
                    ny_start = display.get_cell_y_from_point(height - y_offset)
                    cheight = ny_start - y_start
                    ncontext.rectangle(x_start, y_start, x_end, cheight)
                    ncontext.clip()
                # When the user scrolls the canvas up
                if y_offset < 0:
                    ny_end = display.get_cell_y_from_point(y_start - y_offset)
                    cheight = display.get_cell_height_from_point(y_start - y_offset)
                    ncontext.rectangle(x_start, ny_end + cheight, x_end, y_end)
                    ncontext.clip()

                ncontext.translate(rcache['x_trans'], rcache['y_trans'])
                ncontext.set_source_surface(rcache['surface'], -x_offset, -y_offset)
                ncontext.paint()
                ncontext.reset_clip()
                ncontext.translate(-rcache['x_trans'], -rcache['y_trans'])

                rcache['width']  = width
                rcache['height'] = height
                rcache['x_trans'] = 0
                rcache['y_trans'] = 0

            ccontext = ncontext
            rcache['surface'] = nsurface
            rcache['x_pos'] = display.scroll_x_position
            rcache['y_pos'] = display.scroll_y_position

        self._setup_cairo_context(ccontext)

        # Use system default font family for drawing text
        font_desc = canvas.get_pango_context().get_font_description()
        font_family = font_desc.get_family() if font_desc else 'Sans'
#       head_font_desc = f'{font_family} Normal Bold {display.FONT_SIZE}px #tnum=1'
#       head_font_desc = Pango.font_description_from_string(head_font_desc)
        body_font_desc = f'{font_family} Normal Regular {display.FONT_SIZE}px #tnum=1'
        body_font_desc = Pango.font_description_from_string(body_font_desc)

        layout = PangoCairo.create_layout(ccontext)
        layout.set_wrap(Pango.WrapMode.NONE)
        layout.set_font_description(body_font_desc)

        ccontext.save()
        ccontext.rectangle(x_start, y_start, x_end, y_end)
        ccontext.clip()

        # We use the same color scheme as the headers
        if self.prefers_dark:
            ccontext.set_source_rgb(1.0, 1.0, 1.0)
        else:
            ccontext.set_source_rgb(0.0, 0.0, 0.0)

        col_index = display.get_starting_column()
        x = display.get_cell_x_from_column(col_index)

        bbox = document.bounding_box

        while x < x_end:
            if bbox.column + bbox.column_span - 1 < col_index:
                break # skip out of bound area

            lcol_index = display.get_lcolumn_from_column(col_index)
            cell_width = display.get_cell_width_from_column(col_index)

            if col_index < bbox.column:
                x += cell_width
                col_index += 1
                continue # skip out of bound area

#           layout.set_font_description(body_font_desc)

            ccontext.save()
            ccontext.rectangle(x, display.top_locator_height, cell_width - 2, height)
            ccontext.clip()

            row_index = display.get_starting_row()
            y = display.get_cell_y_from_row(row_index)

            layout_width = cell_width - (2 * display.DEFAULT_CELL_PADDING)
            layout.set_width(layout_width * Pango.SCALE)

            while y < y_end:
                if bbox.row + bbox.row_span - 1 < row_index:
                    break # skip out of bound area

                lrow_index = display.get_lrow_from_row(row_index)
                cell_height = display.get_cell_height_from_row(row_index)

                if (
                    use_cache and
                    (
                        ((x_offset == 0 or y_offset == 0) and (y      < ny_start or
                                                               ny_end < y        or
                                                               x      < nx_start or
                                                               nx_end < x))
                        or ((x_offset > 0 and y_offset > 0) and (x      < nx_start and y      < ny_start))
                        or ((x_offset < 0 and y_offset < 0) and (nx_end < x        and ny_end < y       ))
                        or ((x_offset > 0 and y_offset < 0) and (x      < nx_start and ny_end < y       ))
                        or ((x_offset < 0 and y_offset > 0) and (nx_end < x        and y      < ny_start))
                    )
                ):
                    y += cell_height
                    row_index += 1
                    continue # skip cached area

                if row_index < bbox.row:
                    y += cell_height
                    row_index += 1
                    continue # skip out of bound area

                cell_value = document.read_data(lcol_index, lrow_index)

                # Determine cell data type to decide how to render it properly
                _is_none = cell_value is None
                _is_string = not _is_none and isinstance(cell_value, str)
                _is_numeric = not _is_string and (isinstance(cell_value, (int, float, Decimal)))
                _is_temporal = not _is_numeric and isinstance(cell_value, (date, time, datetime))
                _is_an_object = not (_is_none or _is_string or _is_numeric or _is_temporal)

                # We don't natively support object types, but in any case the user has perfomed
                # an operation that returned an object, we want to show it properly in minimal.
                if _is_an_object:
                    match cell_value:
                        case _ if isinstance(cell_value, timedelta):
                            cell_value = print_timedelta(cell_value)
                        case __:
                            cell_value = '#VALUE!' # f'[<{type(cell_value).__name__}>]'

                if cell_value in {'', None}:
                    y += cell_height
                    row_index += 1
                    continue # skip empty cell

                # Right-align numeric and temporal values
                if _is_numeric or _is_temporal:
                    layout.set_alignment(Pango.Alignment.RIGHT)

                # Otherwise keep it left-aligned
                else:
                    layout.set_alignment(Pango.Alignment.LEFT)

                cell_text = str(cell_value)

                # Truncate the contents for performance reasons
                cell_text = cell_text[:int(cell_width * 0.2)] # 0.2 is a magic number

                # Truncate before the first line break to prevent overflow
                # and make the newlines obvious to the users by displaying
                # it using bent arrow character
                if '\n' in cell_text:
                    cell_text = cell_text.split('\n', 1)[0]
#                   cell_text += '\u21B5'

                # Make the tab characters visible to the users
#               cell_text = cell_text.replace('\t', '\u21E5')

                # Make the whitespaces obvious to the users by
                # replacing them with middle dot characters
#               repl = lambda m: m.group(0).replace(' ', '\u00B7')
#               cell_text = WHITESPACE_PATTERN.sub(repl, cell_text)

                layout.set_text(cell_text, -1)

                x_text = x + display.DEFAULT_CELL_PADDING
                ccontext.move_to(x_text, y + 2)

                PangoCairo.show_layout(ccontext, layout)

#               if lrow_index == 1:
#                   layout.set_font_description(body_font_desc)

                y += cell_height
                row_index += 1

            x += cell_width
            col_index += 1

            ccontext.restore()

        ccontext.restore()

        context.set_source_surface(rcache['surface'], 0, 0)
        context.paint()

    def _draw_cells_borders(self,
                            context: Context,
                            width:   int,
                            height:  int,
                            display: SheetDisplay,
                            ) ->     None:
        """"""
        context.save()

        # We need to make sure that the cell borders are contrast enough
        if self.prefers_dark:
            context.set_source_rgb(0.25, 0.25, 0.25)
        else:
            context.set_source_rgb(0.75, 0.75, 0.75)

        # I bet this is better than a thick line!
        context.set_hairline(True)

        x_start = display.left_locator_width
        y_start = display.top_locator_height

        # Draw separator line between headers and contents
        context.move_to(0, y_start)
        context.line_to(width, y_start)
        context.move_to(x_start, 0)
        context.line_to(x_start, height)
        context.stroke()

        # Draw horizontal lines
        context.reset_clip()
        context.rectangle(0,
                          display.top_locator_height,
                          width,
                          height)
        context.clip()

        nrow_index = display.get_starting_row()
        prow_index = nrow_index

        y = display.get_cell_y_from_row(nrow_index)

        # Prevent showing double lines at the first row
        # when the logical cell right above it is visible
        if nrow_index > 1:
            lrow_index = display.get_lrow_from_row(nrow_index)
            if display.check_cell_visibility_from_position(lrow_index - 1, -1):
                prow_index = lrow_index

        while y < height:
            lrow_index = display.get_lrow_from_row(nrow_index)
            hidden_row_exists = prow_index != lrow_index

            if hidden_row_exists:
                prow_index = lrow_index

            double_lines = hidden_row_exists

            # Draw line(s) in the locator area
            if double_lines:
                context.move_to(0, y - 2)
                context.line_to(x_start, y - 2)
                context.move_to(0, y + 2)
                context.line_to(x_start, y + 2)
            else:
                context.move_to(0, y)
                context.line_to(x_start, y)

            # Draw line in the content area
            context.move_to(x_start, y)
            context.line_to(width, y)

            y += display.get_cell_height_from_row(nrow_index)
            nrow_index += 1
            prow_index += 1

        context.stroke()

        # Draw vertical lines
        context.reset_clip()
        context.rectangle(display.left_locator_width,
                          0,
                          width,
                          height)
        context.clip()

        ncol_index = display.get_starting_column()
        pcol_index = ncol_index

        x = display.get_cell_x_from_column(ncol_index)

        # Prevent showing double lines at the first column
        # when the logical cell right before it is visible
        if ncol_index > 1:
            lcol_index = display.get_lcolumn_from_column(ncol_index)
            if display.check_cell_visibility_from_position(lcol_index - 1, -1):
                pcol_index = lcol_index

        while x < width:
            lcol_index = display.get_lcolumn_from_column(ncol_index)
            hidden_column_exists = pcol_index != lcol_index

            if hidden_column_exists:
                pcol_index = lcol_index

            double_lines = hidden_column_exists

            # Draw line(s) in the locator area
            if double_lines:
                context.move_to(x - 2, 0)
                context.line_to(x - 2, y_start)
                context.move_to(x + 2, 0)
                context.line_to(x + 2, y_start)
            else:
                context.move_to(x, 0)
                context.line_to(x, y_start)

            # Draw line in the content area
            context.move_to(x, y_start)
            context.line_to(x, height)

            x += display.get_cell_width_from_column(ncol_index)
            ncol_index += 1
            pcol_index += 1

        context.stroke()

        context.restore()

    def _draw_selection_borders(self,
                                context:   Context,
                                width:     int,
                                height:    int,
                                display:   SheetDisplay,
                                selection: SheetSelection,
                                ) ->       None:
        """"""
        context.save()

        arange = selection.current_active_range
        range_x, range_y, range_width, range_height = self._get_selection_range(arange.x,
                                                                                arange.y,
                                                                                arange.width,
                                                                                arange.height,
                                                                                width,
                                                                                height,
                                                                                display)

        # Clipping for when the user selects the entire row(s). You may notice that
        # I didn't adjust the width and height as it's not worth the complexity.
        if arange.column == 0:
            context.rectangle(0,
                              display.top_locator_height - 1,
                              width,
                              height)
            context.clip()
        # Clipping for when the user selects the entire column(s)
        if arange.row == 0:
            context.rectangle(display.left_locator_width - 1,
                              0,
                              width,
                              height)
            context.clip()
        # Clipping for general use cases
        if arange.column > 0 and arange.row > 0:
            context.rectangle(display.left_locator_width - 1,
                              display.top_locator_height - 1,
                              width,
                              height)
            context.clip()

        # We use a bold style here
        context.set_source_rgba(*self.color_accent)
        context.set_line_width(2)

        # Indicates that the user has selected the entire column(s) by drawing a vertical line
        # next to the row headers
        if arange.column > 0 and arange.row == 0:
            context.move_to(display.left_locator_width, display.top_locator_height - 1)
            context.line_to(display.left_locator_width, height)
            context.stroke()

        # Indicates that the user has selected the entire row(s) by drawing a horizontal line
        # next to the column headers
        if arange.column == 0 and arange.row > 0:
            context.move_to(display.left_locator_width - 1, display.top_locator_height)
            context.line_to(width, display.top_locator_height)
            context.stroke()

        # Indicates that the user has a selection by drawing a line next to the row and column header(s)
        if arange.column > 0 and arange.row > 0:
            context.move_to(range_x, display.top_locator_height)
            context.line_to(range_x + range_width, display.top_locator_height)
            context.move_to(display.left_locator_width, range_y)
            context.line_to(display.left_locator_width, range_y + range_height)
            context.stroke()

        # Don't render the active selection when the user selects the entire sheet
        if not (range_x == 0 and range_y == 0):
            context.rectangle(range_x,
                              range_y,
                              range_width - 1,
                              range_height - 1)
            context.stroke()

        context.restore()

    def _get_selection_range(self,
                             range_x:       int,
                             range_y:       int,
                             range_width:   int,
                             range_height:  int,
                             canvas_width:  int,
                             canvas_height: int,
                             display:       SheetDisplay,
                             auto_offset:   bool = True,
                             ) ->           tuple[int, int, int, int]:
            """"""
            if range_width < 0:
                range_width = canvas_width
            if range_height < 0:
                range_height = canvas_height

            # Hide the top of the selection if it is exceeded by the scroll viewport
            if range_y < 0:
                range_height += range_y
                range_y = display.top_locator_height
                range_height -= display.top_locator_height
            # Hide the entire selection if it is exceeded by the scroll viewport
            if range_height < 0:
                range_height = 0
            # Hide the entire selection if the viewport has not reached it yet
            if canvas_height < range_y:
                range_y = canvas_height + 1
                range_height = 0
            # Hide the bottom of the selection if it is not yet in the viewport
            if canvas_height < range_y + range_height:
                range_height = canvas_height - range_y

            # Hide the left of the selection if it is exceeded by the scroll viewport
            if range_x < 0:
                range_width += range_x
                range_x = display.left_locator_width
                range_width -= display.left_locator_width
            # Hide the entire selection if it is exceeded by the scroll viewport
            if range_width < 0:
                range_width = 0
            # Hide the entire selection if the viewport has not reached it yet
            if canvas_width < range_x:
                range_x = canvas_width + 1
                range_width = 0
            # Hide the right of the selection if it is not yet in the viewport
            if canvas_width < range_x + range_width:
                range_width = canvas_width - range_x

            if auto_offset:
                if range_x == 0:
                    range_x = 1
                    range_width -= 1
                if range_y == 0:
                    range_y = 1
                    range_height -= 1

            return range_x, range_y, range_width, range_height

from .canvas import SheetCanvas
