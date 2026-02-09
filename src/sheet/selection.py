# selection.py
#
# Copyright (c) 2025 Naufan Rusyda Faikar
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from gi.repository import Gdk
from gi.repository import Gtk
from typing import Literal
from typing import TypeAlias

from ..core.datatable import DataTable

CType: TypeAlias = Literal['top', 'left', 'corner', 'content']

class SheetCell():

    def __init__(self,

                 # Geometry
                 x:             int   = 0,
                 y:             int   = 0,
                 width:         int   = 0,
                 height:        int   = 0,

                 # Table
                 column:        int   = 0,
                 row:           int   = 0,
                 column_span:   int   = 0,
                 row_span:      int   = 0,

                 # Direction
                 right_to_left: bool  = False,
                 bottom_to_top: bool  = False,

                 # Metadata
                 mrow:          int   = 0,
                 mcolumn:       int   = 0,
                 mdfi:          int   = -1,

                 ctype:         CType = 'content',
    ) -> None:
        """"""
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.column = column
        self.row = row
        self.column_span = column_span
        self.row_span = row_span

        self.right_to_left = right_to_left
        self.bottom_to_top = bottom_to_top

        self.mcolumn = mcolumn
        self.mrow = mrow
        self.mdfi = mdfi

        self.ctype = ctype


class SheetSelection():

    current_cell_name:   str = None
    previous_cell_name:  str = None

    previous_cell_data:  str = None
    current_cell_data:   str = None

    previous_cell_dtype: str = None
    current_cell_dtype:  str = None

    previous_active_range: SheetCell = SheetCell()
    current_active_range:  SheetCell = SheetCell()

    previous_active_cell:  SheetCell = SheetCell()
    current_active_cell:   SheetCell = SheetCell()

    previous_cursor_cell:  SheetCell = SheetCell()
    current_cursor_cell:   SheetCell = SheetCell()

    current_search_range:  SheetCell = SheetCell()
    current_cutcopy_range: SheetCell = SheetCell()

    def __init__(self,
                 document: 'SheetDocument',
                 display:  'SheetDisplay',
                 view:     'SheetView' = None,
                 ) ->      'None':
        """"""
        self.document = document
        self.display  = display
        self.view     = view

    def update_from_name(self,
                         name: str,
                         ) ->  None:
        """"""
        self.previous_cell_name = self.current_cell_name

        lcol_1, lrow_1, lcol_2, lrow_2 = self.display.get_cell_range_from_name(name)

        col_1 = self.display.get_column_from_lcolumn(lcol_1)
        col_2 = self.display.get_column_from_lcolumn(lcol_2)
        row_1 = self.display.get_row_from_lrow(lrow_1)
        row_2 = self.display.get_row_from_lrow(lrow_2)

        self.update_from_position(col_1,
                                  row_1,
                                  col_2,
                                  row_2,
                                  follow_cursor = False)

    def update_from_point(self,
                          event:   Gtk.GestureClick,
                          n_press: int,
                          x:       float,
                          y:       float,
                          ) ->     None:
        """"""
        column = self.display.get_column_from_point(x)
        row = self.display.get_row_from_point(y)

        col_1 = column
        row_1 = row
        col_2 = column
        row_2 = row

        state = event.get_current_event_state()
        if state & Gdk.ModifierType.SHIFT_MASK:
            active = self.current_active_cell
            col_1 = active.column
            row_1 = active.row

        self.update_from_position(col_1,
                                  row_1,
                                  col_2,
                                  row_2,
                                  keep_order  = True,
                                  auto_scroll = False)

    def update_by_motion(self,
                         x:           int,
                         y:           int,
                         auto_scroll: bool = False,
                         ) ->         None:
        """"""
        active_range = self.current_active_range
        range_column = active_range.column
        range_row = active_range.row

        # Automatically adjust when the entire sheet is selected
        if range_column == 0 and range_row == 0:
            return

        active_cell = self.current_active_cell

        cursor_cell = self.current_cursor_cell
        cursor_column = cursor_cell.column
        cursor_row = cursor_cell.row

        col_1 = active_cell.column
        row_1 = active_cell.row
        col_2 = self.display.get_column_from_point(x)
        row_2 = self.display.get_row_from_point(y)

        # Prevent the user from selecting locator cells undesirably
        # and also from unwanted scroll jumping. We may also want to
        # decrease the sensivity of the autoscroll for this case.
        if active_range.ctype != 'content':
            if active_range.ctype == 'top':
                row_1 = 0
                row_2 = 0
                if col_2 <= 0:
                    col_2 = max(1, cursor_column - 1)

            if active_range.ctype == 'left':
                col_1 = 0
                col_2 = 0
                if row_2 <= 0:
                    row_2 = max(1, cursor_row - 1)

        else:
            if col_2 <= 0:
                col_2 = max(1, cursor_column - 1)
            if row_2 <= 0:
                row_2 = max(1, cursor_row - 1)

        # Skip if the cursor is not considered moving
        if col_2 == cursor_column \
                and row_2 == cursor_row:
            return
        if col_2 == cursor_column \
                and row_2 == 0 \
                and cursor_row == 1:
            return
        if col_2 == 0 \
                and cursor_column == 1 \
                and row_2 == cursor_row:
            return

        self.update_from_position(col_1,
                                  row_1,
                                  col_2,
                                  row_2,
                                  keep_order  = True,
                                  auto_scroll = auto_scroll)

    def update_by_keypress(self,
                           keyval: int,
                           state:  Gdk.ModifierType,
                           ) ->    None:
        """"""
        active_cell = self.current_active_cell
        cursor_cell = self.current_cursor_cell

        active_position = (active_cell.column, active_cell.row)
        cursor_position = (cursor_cell.column, cursor_cell.row)
        target_position = active_position

        lcolumn = self.display.get_lcolumn_from_column(active_cell.column)
        lrow = self.display.get_lrow_from_row(active_cell.row)

        focused_table = self.document.get_table_by_position(lcolumn, lrow)
        table_bbox = focused_table.bounding_box \
                     if isinstance(focused_table, DataTable) \
                     else None

        # TODO: if the cursor in a blank cell, it should find nearest non-blank
        # cell when pressing Control plus arrow keys.

        match keyval:
            case Gdk.KEY_Tab | Gdk.KEY_ISO_Left_Tab:
                # Select a cell at the left to the selection
                if state & Gdk.ModifierType.SHIFT_MASK:
                    target_position = (active_position[0] - 1,
                                       active_position[1])

                    # If the cursor is currently within a table and it's reaching the first column,
                    # re-target to the last column of the previous row instead.
                    if table_bbox and target_position[0] == 0 and target_position[1] > 1:
                        target_position = (table_bbox.column + table_bbox.column_span - 1,
                                           target_position[1] - 1)

                # Select a cell at the right to the selection
                else:
                    target_position = (active_position[0] + 1,
                                       active_position[1])

                    # If the cursor is currently within a table and it's reaching the last column,
                    # re-target to the first column of the next row instead.
                    if table_bbox and table_bbox.column + table_bbox.column_span - 1 < target_position[0]:
                        target_position = (1, # first column
                                           target_position[1] + 1)

            case Gdk.KEY_Return:
                # Select a cell at the bottom to the selection
                if state & Gdk.ModifierType.SHIFT_MASK:
                    target_position = (active_position[0],
                                       active_position[1] - 1)

                # Select a cell at the top to the selection
                else:
                    target_position = (active_position[0],
                                       active_position[1] + 1)

            case Gdk.KEY_Left:
                # Include all cells to the left to the selection
                if (state & Gdk.ModifierType.SHIFT_MASK) and (state & Gdk.ModifierType.CONTROL_MASK):
                    if table_bbox and table_bbox.column < target_position[0]:
                        cursor_position = (table_bbox.column,
                                           cursor_position[1])
                        target_position = (active_position,
                                           cursor_position)
                    else:
                        cursor_position = (1, cursor_position[1])
                        target_position = (active_position,
                                           cursor_position)

                # Select the leftmost cell in the same row
                elif state & Gdk.ModifierType.CONTROL_MASK:
                    if table_bbox and table_bbox.column < target_position[0]:
                        target_position = (table_bbox.column,
                                           active_position[1])
                    else:
                        target_position = (1, # first column
                                           active_position[1])

                # Include a cell at the left to the selection
                elif state & Gdk.ModifierType.SHIFT_MASK:
                    cursor_position = (cursor_position[0] - 1,
                                       cursor_position[1])
                    target_position = (active_position,
                                       cursor_position)

                # Select a cell at the left to the selection
                else:
                    target_position = (active_position[0] - 1,
                                       active_position[1])

            case Gdk.KEY_Right:
                # Include all cells to the right to the selection
                if (state & Gdk.ModifierType.SHIFT_MASK) and (state & Gdk.ModifierType.CONTROL_MASK):
                    if table_bbox and target_position[0] < table_bbox.column + table_bbox.column_span - 1:
                        cursor_position = (table_bbox.column + table_bbox.column_span - 1,
                                           cursor_position[1])
                        target_position = (active_position,
                                           cursor_position)
                    else:
                        cursor_position = (cursor_position[0] + 1,
                                           cursor_position[1])
                        target_position = (active_position,
                                           cursor_position)

                # Select the rightmost cell in the same row
                elif state & Gdk.ModifierType.CONTROL_MASK:
                    if table_bbox and target_position[0] < table_bbox.column + table_bbox.column_span - 1:
                        target_position = (table_bbox.column + table_bbox.column_span - 1,
                                           active_position[1])
                    else:
                        target_position = (active_position[0] + 1,
                                           active_position[1])

                # Include a cell at the right to the selection
                elif state & Gdk.ModifierType.SHIFT_MASK:
                    cursor_position = (cursor_position[0] + 1,
                                       cursor_position[1])
                    target_position = (active_position,
                                       cursor_position)

                # Select a cell at the right to the selection
                else:
                    target_position = (active_position[0] + 1,
                                       active_position[1])

            case Gdk.KEY_Up:
                # Include all cells above to the selection
                if (state & Gdk.ModifierType.SHIFT_MASK) and (state & Gdk.ModifierType.CONTROL_MASK):
                    if table_bbox and table_bbox.row < target_position[1]:
                        cursor_position = (cursor_position[0],
                                           table_bbox.row)
                        target_position = (active_position,
                                           cursor_position)
                    else:
                        cursor_position = (cursor_position[0],
                                           1) # first row
                        target_position = (active_position,
                                           cursor_position)

                # Select the topmost cell in the same column
                elif state & Gdk.ModifierType.CONTROL_MASK:
                    if table_bbox and table_bbox.row < target_position[1]:
                        target_position = (active_position[0],
                                           table_bbox.row)
                    else:
                        target_position = (active_position[0],
                                           1) # first row

                # Include a cell at the top to the selection
                elif state & Gdk.ModifierType.SHIFT_MASK:
                    cursor_position = (cursor_position[0],
                                       cursor_position[1] - 1)
                    target_position = (active_position,
                                       cursor_position)

                # Select a cell at the top to the selection
                else:
                    target_position = (active_position[0],
                                       active_position[1] - 1)

            case Gdk.KEY_Down:
                # Include all cells below to the selection
                if (state & Gdk.ModifierType.SHIFT_MASK) and (state & Gdk.ModifierType.CONTROL_MASK):
                    if table_bbox and target_position[1] < table_bbox.row + table_bbox.row_span - 1:
                        cursor_position = (cursor_position[0],
                                           table_bbox.row + table_bbox.row_span - 1)
                        target_position = (active_position,
                                           cursor_position)
                    else:
                        cursor_position = (cursor_position[0],
                                           cursor_position[1] + 1)
                        target_position = (active_position,
                                           cursor_position)

                # Select the bottommost cell in the same column
                elif state & Gdk.ModifierType.CONTROL_MASK:
                    if table_bbox and target_position[1] < table_bbox.row + table_bbox.row_span - 1:
                        target_position = (active_position[0],
                                           table_bbox.row + table_bbox.row_span - 1)
                    else:
                        target_position = (active_position[0],
                                           active_position[1] + 1)

                # Include a cell at the bottom to the selection
                elif state & Gdk.ModifierType.SHIFT_MASK:
                    cursor_position = (cursor_position[0],
                                       cursor_position[1] + 1)
                    target_position = (active_position,
                                       cursor_position)

                # Select a cell at the bottom to the selection
                else:
                    target_position = (active_position[0],
                                       active_position[1] + 1)

        if all(isinstance(i, int) for i in target_position):
            col_1, row_1 = target_position
            col_2, row_2 = col_1, row_1
        else:
            (col_1, row_1), (col_2, row_2) = target_position

        col_1 = max(1, col_1)
        row_1 = max(1, row_1)
        col_2 = max(1, col_2)
        row_2 = max(1, row_2)

        self.update_from_position(col_1,
                                  row_1,
                                  col_2,
                                  row_2,
                                  keep_order = True)

    def update_from_position(self,
                             col_1:         int,
                             row_1:         int,
                             col_2:         int,
                             row_2:         int,
                             keep_order:    bool = False,
                             follow_cursor: bool = True,
                             auto_scroll:   bool = True,
                             scroll_axis:   str  = 'both',
                             ) ->           None:
        """"""
        # Handle a special case when the user inputs e.g. "A:1" or "1:A"
        # which we want to interpret as selecting the entire sheet
        if col_1 == row_2 == 0 or row_1 == col_2 == 0:
            col_1 = row_1 = col_2 = row_2 = 0

        start_column = min(col_1, col_2)
        start_row = min(row_1, row_2)

        end_column = max(col_1, col_2)
        end_row = max(row_1, row_2)

        x = self.display.get_cell_x_from_column(start_column)
        y = self.display.get_cell_y_from_row(start_row)

        end_x = self.display.get_cell_x_from_column(end_column)
        end_y = self.display.get_cell_y_from_row(end_row)

        end_width = self.display.get_cell_width_from_column(end_column)
        end_height = self.display.get_cell_height_from_row(end_row)

        width = end_x + end_width - x
        height = end_y + end_height - y

        column_span = end_column - start_column + 1
        row_span = end_row - start_row + 1

        right_to_left = col_2 < col_1
        bottom_to_top = row_2 < row_1

        mrow = -1
        mcolumn = -1
        mdfi = -1

        # Cache the previous active range, usually to prevent
        # from unnecessary re-renders
        self.previous_active_range = self.current_active_range
        self.previous_active_cell  = self.current_active_cell

        # Handle clicking on the top left locator area
        if start_column == 0 and start_row == 0:
            self.current_active_range = SheetCell(x             = x,
                                                  y             = y,
                                                  width         = -1,
                                                  height        = -1,
                                                  column        = 0,
                                                  row           = 0,
                                                  column_span   = -1,
                                                  row_span      = -1,
                                                  right_to_left = right_to_left,
                                                  bottom_to_top = bottom_to_top,
                                                  mrow          = mrow,
                                                  mcolumn       = mcolumn,
                                                  mdfi          = mdfi,
                                                  ctype         = 'corner')

        # Handle selecting the top locator area
        elif start_column > 0 and start_row == 0:
            self.current_active_range = SheetCell(x             = x,
                                                  y             = y,
                                                  width         = width,
                                                  height        = -1,
                                                  column        = start_column,
                                                  row           = 0,
                                                  column_span   = column_span,
                                                  row_span      = -1,
                                                  right_to_left = right_to_left,
                                                  bottom_to_top = bottom_to_top,
                                                  mrow          = mrow,
                                                  mcolumn       = mcolumn,
                                                  mdfi          = mdfi,
                                                  ctype         = 'top')

        # Handle selecting the left locator area
        elif start_column == 0 and start_row > 0:
            self.current_active_range = SheetCell(x             = x,
                                                  y             = y,
                                                  width         = -1,
                                                  height        = height,
                                                  column        = 0,
                                                  row           = start_row,
                                                  column_span   = -1,
                                                  row_span      = row_span,
                                                  right_to_left = right_to_left,
                                                  bottom_to_top = bottom_to_top,
                                                  mrow          = mrow,
                                                  mcolumn       = mcolumn,
                                                  mdfi          = mdfi,
                                                  ctype         = 'left')

        # Handle selecting a cell content area
        else:
            self.current_active_range = SheetCell(x             = x,
                                                  y             = y,
                                                  width         = width,
                                                  height        = height,
                                                  column        = start_column,
                                                  row           = start_row,
                                                  column_span   = column_span,
                                                  row_span      = row_span,
                                                  right_to_left = right_to_left,
                                                  bottom_to_top = bottom_to_top,
                                                  mrow          = mrow,
                                                  mcolumn       = mcolumn,
                                                  mdfi          = mdfi,
                                                  ctype         = 'content')

        if self.current_active_range.ctype != 'content':
            col_1 = max(1, col_1)
            row_1 = max(1, row_1)
            col_2 = max(1, col_2)
            row_2 = max(1, row_2)
            start_column = max(1, start_column)
            start_row = max(1, start_row)
            end_column = max(1, end_column)
            end_row = max(1, end_row)

        if not keep_order:
            col_1 = start_column
            row_1 = start_row
            col_2 = end_column
            row_2 = end_row

        x = self.display.get_cell_x_from_column(col_1)
        y = self.display.get_cell_y_from_row(row_1)
        width = self.display.get_cell_width_from_column(col_1)
        height = self.display.get_cell_height_from_row(row_1)
        self.current_active_cell = SheetCell(x             = x,
                                             y             = y,
                                             width         = width,
                                             height        = height,
                                             column        = col_1,
                                             row           = row_1,
                                             column_span   = 1,
                                             row_span      = 1,
                                             right_to_left = False,
                                             bottom_to_top = False,
                                             mrow          = mrow,
                                             mcolumn       = mcolumn,
                                             mdfi          = mdfi,
                                             ctype         = 'content')

        x = self.display.get_cell_x_from_column(col_2)
        y = self.display.get_cell_y_from_row(row_2)
        width = self.display.get_cell_width_from_column(col_2)
        height = self.display.get_cell_height_from_row(row_2)
        self.current_cursor_cell = SheetCell(x             = x,
                                             y             = y,
                                             width         = width,
                                             height        = height,
                                             column        = col_2,
                                             row           = row_2,
                                             column_span   = 1,
                                             row_span      = 1,
                                             right_to_left = False,
                                             bottom_to_top = False,
                                             mrow          = mrow,
                                             mcolumn       = mcolumn,
                                             mdfi          = mdfi,
                                             ctype         = 'content')

        if auto_scroll:
            self.view.update_by_selection(follow_cursor, scroll_axis)

        lcolumn = self.display.get_lcolumn_from_column(col_1)
        lrow = self.display.get_lrow_from_row(row_1)

        cell_name = self.display.get_cell_name_from_position(lcolumn, lrow)
        cell_data, cell_dtype = self.document.read_data(lcolumn, lrow, with_dtype = True)

        self.previous_cell_name  = self.current_cell_name
        self.previous_cell_data  = self.current_cell_data
        self.previous_cell_dtype = self.current_cell_dtype

        self.current_cell_name   = cell_name
        self.current_cell_data   = cell_data
        self.current_cell_dtype  = cell_dtype

        canvas = self.view.Canvas
        editor = canvas.get_editor()
        editor.refresh_ui(refresh = False)

    def update_by_scroll(self) -> None:
        """"""
        column = self.current_active_range.column
        row = self.current_active_range.row
        self.current_active_range.x = self.display.get_cell_x_from_column(column)
        self.current_active_range.y = self.display.get_cell_y_from_row(row)

        column = self.current_active_cell.column
        row = self.current_active_cell.row
        self.current_active_cell.x = self.display.get_cell_x_from_column(column)
        self.current_active_cell.y = self.display.get_cell_y_from_row(row)

        canvas = self.view.Canvas
        editor = canvas.get_editor()
        editor.queue_draw()

from .document import SheetDocument
from .display import SheetDisplay
from .view import SheetView
