# display.py
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

from polars import Boolean
from polars import Series
from polars import UInt32
import re

class SheetDisplay():

    DEFAULT_CELL_HEIGHT:  int = 20
    DEFAULT_CELL_WIDTH:   int = 65
    DEFAULT_CELL_PADDING: int = 6

    ICON_SIZE: float = 18
    FONT_SIZE: float = 12

    left_locator_width: int = 45
    top_locator_height: int = 20

    pan_increment:    int = 0.05
    scroll_increment: int = 3
    page_increment:   int = 20

    scroll_y_position: int = 0
    scroll_x_position: int = 0

    # Holds the visibility flags for each row and column.
    # The row vflags includes the virtual row for the
    # dataframe header.
    row_vflags:    Series = Series(dtype = Boolean)
    column_vflags: Series = Series(dtype = Boolean)

    # Holds the visible indices for each row and column,
    # starts from 0. It should be less or equals to the
    # length of the visibility flags.
    row_vseries:    Series = Series(dtype = UInt32)
    column_vseries: Series = Series(dtype = UInt32)

    # Holds the height and width of each row and column.
    row_heights:   Series = Series(dtype = UInt32)
    column_widths: Series = Series(dtype = UInt32)

    # Holds the cumulative height and width of each
    # visible row and column. These also are used
    # for calculating canvas scroll bounding box.
    crow_heights:   Series = Series(dtype = UInt32)
    ccolumn_widths: Series = Series(dtype = UInt32)

    def reset(self) -> None:
        """"""
        self.row_vflags   = Series(dtype = Boolean)
        self.row_vseries  = Series(dtype = UInt32)
        self.row_heights  = Series(dtype = UInt32)
        self.crow_heights = Series(dtype = UInt32)

        self.column_vflags  = Series(dtype = Boolean)
        self.column_vseries = Series(dtype = UInt32)
        self.column_widths  = Series(dtype = UInt32)
        self.ccolumn_widths = Series(dtype = UInt32)

    def get_lcolumn_from_column(self,
                                column: int,
                                ) ->    int:
        """Get the logical column index from the visual column index."""
        # The prefix "l" in "lcolumn" and "lrow" stands for "logical", applicable for when there are
        # hidden columns/rows. The parameter `column` here is the one that refers to the visible column.
        # For the explanation of this function, please read the docstring in the get_lrow_from_row().
        if column == 0: # for the locator
            return 0

        if len(self.column_vflags) == 0:
            return column # every columns is visible

        if len(self.column_vflags) == len(self.column_vseries):
            return column # every columns is visible

        if len(self.column_vseries) == 0:
            return len(self.column_vflags) + column

        if column <= len(self.column_vseries):
            return self.column_vseries[column - 1] + 1

        return len(self.column_vflags) + (column - len(self.column_vseries))

    def get_lrow_from_row(self,
                          row: int,
                          ) -> int:
        """Get the logical row index from the visual row index."""
        # Since the column and row locators are always visible and they are always at the index of 0,
        # we can just simply return 0 if the `row` paramater is also 0. Note that the locators are
        # never referenced by the visibility flags. Anything else always acquire cells at index >= 1.
        if row == 0: # for the locator
            return 0

        # When the column/row visibility flags is empty (or unset), there's not any hidden rows.
        # So we just simply returns the `row` parameter back.
        if len(self.row_vflags) == 0:
            return row # every rows is visible

        # When the column/row visibility flags isn't empty, we need to calculate the real column/row
        # index based on the flags. The column/row visible series contains the real index of the
        # visible column/row, starting from 0, won't include the locator as we've talked. The visible
        # series will never have more items than the visibility flags; it can be less or equals to.
        if len(self.row_vflags) == len(self.row_vseries):
            return row # every rows is visible

        # In a rare occassion, the column/row visible series can be empty. But well, in our current
        # implementation, we'll always have the header of the main dataframe at the row index of 1.
        # As we unable to hide the header row, so the series will always contains 1 item at minimum.
        # But for safety and reusability, we want to always check if the series is empty or not.
        if len(self.row_vseries) == 0:
            return len(self.row_vflags) + row
            # Since we only support a single main dataframe and the current implementation will flag
            # all the rows in the main dataframe including the header row, this condition also means
            # that the entire dataframe is invisible. Once again, this condition isn't reachable.
            # But for the column, it's different despite making no senses to hide all of them.

        # The other two possible chances are the user selects any visible cell within the dataframe
        # bounding box or outside the bounding box.
        if row <= len(self.row_vseries):
            return self.row_vseries[row - 1] + 1
            # -1 because content starts from row 1
            # +1 because the vseries starts from 0

        return len(self.row_vflags) + (row - len(self.row_vseries))

    def get_column_from_lcolumn(self,
                                lcolumn: int,
                                ) ->     int:
        """Get the visual column index from the logical column index."""
        if lcolumn == 0: # for the locator
            return 0

        if len(self.column_vflags) == 0:
            return lcolumn # every columns is visible

        if len(self.column_vflags) == len(self.column_vseries):
            return lcolumn # every columns is visible

        # All columns within the dataframe bounding box are hidden
        if len(self.column_vseries) == 0:
            if lcolumn <= len(self.column_vflags):
                return -1 # requested column is hidden
            return lcolumn - len(self.column_vflags)

        # Some columns within the dataframe bounding box are hidden
        if lcolumn <= len(self.column_vflags):
            if not self.column_vflags[lcolumn - 1]:
                return -1 # requested column is hidden
            return self.column_vseries.search_sorted(lcolumn - 1, 'left') + 1

        # Request columns outside the dataframe bounding box
        return lcolumn - (len(self.column_vflags) - len(self.column_vseries))

    def get_row_from_lrow(self,
                          lrow: int,
                          ) ->  int:
        """Get the visual row index from the logical row index."""
        if lrow == 0: # for the locator
            return 0

        if len(self.row_vflags) == 0:
            return lrow # every rows is visible

        if len(self.row_vflags) == len(self.row_vseries):
            return lrow # every rows is visible

        # All rows within the dataframe bounding box are hidden
        if len(self.row_vseries) == 0:
            if lrow <= len(self.row_vflags):
                return -1 # requested row is hidden
            return lrow - len(self.row_vflags)

        # Some rows within the dataframe bounding box are hidden
        if lrow <= len(self.row_vflags):
            if not self.row_vflags[lrow - 1]:
                return -1 # requested row is hidden
            return self.row_vseries.search_sorted(lrow - 1, 'left') + 1

        # Request rows outside the dataframe bounding box
        return lrow - (len(self.row_vflags) - len(self.row_vseries))

    def get_starting_column(self,
                            offset:       int  = 0,
                            after_scroll: bool = True,
                            ) ->          int:
        """Get the first visual column index that is visible from the given offset."""
        return self.get_column_from_point(offset,
                                          with_locator = False,
                                          after_scroll = after_scroll)

    def get_ending_column(self,
                          width:        int,
                          offset:       int  = 0,
                          after_scroll: bool = True,
                          ) ->          int:
        """Get the last visual column index that is visible from the given offset."""
        index = self.get_starting_column(offset, after_scroll)
        x = self.get_cell_x_from_column(index)
        while x < width:
            x += self.get_cell_width_from_column(index)
            index += 1
        return index - 1

    def get_starting_row(self,
                         offset:       int  = 0,
                         after_scroll: bool = True,
                         ) ->          int:
        """Get the first visual row index that is visible from the given offset."""
        return self.get_row_from_point(offset,
                                       with_locator = False,
                                       after_scroll = after_scroll)

    def get_ending_row(self,
                       height:       int,
                       offset:       int  = 0,
                       after_scroll: bool = True,
                       ) ->          int:
        """Get the last visual row index that is visible from the given offset."""
        index = self.get_starting_row(offset, after_scroll)
        y = self.get_cell_y_from_row(index)
        while y < height:
            y += self.get_cell_height_from_row(index)
            index += 1
        return index - 1

    def get_column_from_point(self,
                              x:            int,
                              with_locator: bool = True,
                              after_scroll: bool = True,
                              ) ->          int:
        """Get the visual column index that is visible from the given point."""
        if with_locator and x <= self.left_locator_width:
            return 0

        if with_locator:
            x -= self.left_locator_width

        if after_scroll:
            x += self.scroll_x_position

        # All columns use the default width
        if len(self.column_widths) == 0:
            return int(x // self.DEFAULT_CELL_WIDTH) + 1

        # Requested column is within the dataframe bounding box
        if x <= self.ccolumn_widths[-1]:
            return self.ccolumn_widths.search_sorted(x, 'left') + 1

        # Requested column is outside the dataframe bounding box
        x -= self.ccolumn_widths[-1]
        column = int(x // self.DEFAULT_CELL_WIDTH) + 1
        return len(self.ccolumn_widths) + column

    def get_row_from_point(self,
                           y:            int,
                           with_locator: bool = True,
                           after_scroll: bool = True,
                           ) ->          int:
        """Get the visual row index that is visible from the given point."""
        if with_locator and y <= self.top_locator_height:
            return 0

        if with_locator:
            y -= self.top_locator_height

        if after_scroll:
            y += self.scroll_y_position

        # All rows use the default height
        if len(self.row_heights) == 0:
            return int(y // self.DEFAULT_CELL_HEIGHT) + 1

        # Requested row is within the dataframe bounding box
        if y <= self.crow_heights[-1]:
            return self.crow_heights.search_sorted(y, 'left') + 1

        # Requested row is outside the dataframe bounding box
        y -= self.crow_heights[-1]
        row = int(y // self.DEFAULT_CELL_HEIGHT) + 1
        return len(self.crow_heights) + row

    def get_cell_x_from_point(self,
                              x:             int,
                              column_offset: int  = 0,
                              with_locator:  bool = True,
                              after_scroll:  bool = True,
                              ) ->           int:
        """Get x from the cell at the given point."""
        column = self.get_column_from_point(x, with_locator, after_scroll) + column_offset
        return self.get_cell_x_from_column(column)

    def get_cell_y_from_point(self,
                              y:            int,
                              row_offset:   int  = 0,
                              with_locator: bool = True,
                              after_scroll: bool = True,
                              ) ->          int:
        """Get y from the cell at the given point."""
        row = self.get_row_from_point(y, with_locator, after_scroll) + row_offset
        return self.get_cell_y_from_row(row)

    def get_cell_x_from_column(self,
                               column: int,
                               ) ->    int:
        """Get x from the cell at the given visual column index."""
        if column == 0: # for the locator
            return 0

        # Apply offset by the locator and scroll position
        x = self.left_locator_width - self.scroll_x_position

        if column == 1: # the first cell
            return x

        # When column widths definition exists
        if df_width := len(self.ccolumn_widths):
            if column <= df_width:
                return x + self.ccolumn_widths[column - 2]
                # -1 because content starts from column 1
                # -1 because column 1 is already handled
            return x + self.ccolumn_widths[-1] \
                     + (column - 1 - df_width) * self.DEFAULT_CELL_WIDTH

        return x + (column - 1) * self.DEFAULT_CELL_WIDTH
        # -1 because content starts from column 1

    def get_cell_y_from_row(self,
                            row: int,
                            ) -> int:
        """Get y from the cell at the given visual row index."""
        if row == 0: # for the locator
            return 0

        # Apply offset by the locator and scroll position
        y = self.top_locator_height - self.scroll_y_position

        if row == 1: # the first cell
            return y

        # When row heights definition exists
        if df_height := len(self.crow_heights):
            if row <= df_height:
                return y + self.crow_heights[row - 2]
                # -1 because content starts from row 1
                # -1 because row 1 is already handled
            return y + self.crow_heights[-1] \
                     + (row - 1 - df_height) * self.DEFAULT_CELL_HEIGHT

        return y + (row - 1) * self.DEFAULT_CELL_HEIGHT
        # -1 because content starts from row 1

    def get_cell_width_from_point(self,
                                  x:            int,
                                  with_locator: bool = True,
                                  after_scroll: bool = True,
                                  ) ->          int:
        """Get the width of the cell at the given point."""
        column = self.get_column_from_point(x, with_locator, after_scroll)
        return self.get_cell_width_from_column(column)

    def get_cell_height_from_point(self,
                                   y:            int,
                                   with_locator: bool = True,
                                   after_scroll: bool = True,
                                   ) ->          int:
        """Get the height of the cell at the given point."""
        row = self.get_row_from_point(y, with_locator, after_scroll)
        return self.get_cell_height_from_row(row)

    def get_cell_width_from_column(self,
                                   column: int,
                                   ) ->    int:
        """Get the width of the cell at the given visual column index."""
        lcolumn = self.get_lcolumn_from_column(column)
        if lcolumn == 0:
            return self.left_locator_width
        if 0 < lcolumn <= len(self.column_widths):
            return self.column_widths[lcolumn - 1]
        return self.DEFAULT_CELL_WIDTH

    def get_cell_height_from_row(self,
                                 row: int,
                                 ) -> int:
        """Get the height of the cell at the given visual row index."""
        lrow = self.get_lrow_from_row(row)
        if lrow == 0:
            return self.top_locator_height
        if 0 < lrow <= len(self.row_heights):
            return self.row_heights[lrow - 1]
        return self.DEFAULT_CELL_HEIGHT

    def get_n_hidden_columns(self,
                             col_1: int,
                             col_2: int,
                             ) ->   int:
        """"""
        if len(self.column_vseries):
            lcol_1 = self.get_column_from_lcolumn(col_1)
            lcol_2 = self.get_column_from_lcolumn(col_2)
            return (col_2 - col_1) - (lcol_2 - lcol_1)
        return 0

    def get_n_all_hidden_columns(self) -> int:
        """"""
        return len(self.column_vflags) - len(self.column_vseries)

    def get_n_hidden_rows(self,
                          row_1: int,
                          row_2: int,
                          ) ->   int:
        """"""
        if len(self.row_vseries):
            lrow_1 = self.get_row_from_lrow(row_1)
            lrow_2 = self.get_row_from_lrow(row_2)
            return (row_2 - row_1) - (lrow_2 - lrow_1)
        return 0

    def get_n_all_hidden_rows(self) -> int:
        """"""
        return len(self.row_vflags) - len(self.row_vseries)

    def check_cell_visibility_from_position(self,
                                            lcolumn: int,
                                            lrow:    int,
                                            ) ->     bool:
        """Check if the cell at the given logical column and row index is visible."""
        is_column_visible = True
        is_row_visible = True

        if 0 < lcolumn and lcolumn <= len(self.column_vflags):
            is_column_visible = self.column_vflags[lcolumn - 1]

        if 0 < lrow and lrow <= len(self.row_vflags):
            is_row_visible = self.row_vflags[lrow - 1]

        return is_column_visible and is_row_visible

    def get_right_cell_name(self,
                            name: str,
                            ) ->  str:
        """"""
        match = re.match(r"([A-Z]+)(\d+)", name, re.IGNORECASE)

        column_part_str = match.group(1).upper()
        row_part = match.group(2)

        chars = list(column_part_str)
        i = len(chars) - 1

        # Iterate from the rightmost character of the column part, handling 'Z' rollovers
        while i >= 0 and chars[i] == 'Z':
            chars[i] = 'A' # Wrap 'Z' to 'A'
            i -= 1 # Move to the left to increment the next character

        # If all characters were 'Z' (e.g. "Z", "ZZ"), add a new 'A' at the beginning
        # e.g. "Z" -> "AA", "ZZ" -> "AAA"
        if i == -1:
            new_column_part = 'A' * (len(chars) + 1)

        # Increment the character at index 'i'
        else:
            chars[i] = chr(ord(chars[i]) + 1)
            new_column_part = ''.join(chars)

        return f"{new_column_part}{row_part}"

    def get_above_cell_name(self,
                            name: str,
                            ) ->  str:
        """"""
        match = re.match(r"([A-Z]+)(\d+)", name, re.IGNORECASE)

        column_part = match.group(1).upper()
        row_part_str = match.group(2)

        try:
            row_number = int(row_part_str)
            if row_number <= 1: # Rows always start from 1
                return "INVALID_ABOVE_CELL"

            new_row_number = row_number - 1
            return f"{column_part}{new_row_number}"

        except ValueError:
            return "INVALID_ROW_NUMBER"

    def get_left_cell_name(self,
                           name: str,
                           ) ->  str:
        """"""
        match = re.match(r"([A-Z]+)(\d+)", name, re.IGNORECASE)

        column_part_str = match.group(1).upper()
        row_part = match.group(2)

        chars = list(column_part_str)
        n = len(chars)
        i = n - 1

        # Iterate from the rightmost character of the column part, handling 'A' rollovers (borrowing)
        while i >= 0:
            if chars[i] == 'A':
                chars[i] = 'Z' # Wrap around to 'Z'
                i -= 1 # Move to the left to "borrow"
            else:
                chars[i] = chr(ord(chars[i]) - 1) # Decrement the character
                break

        # If the loop completes, it means all characters were 'A's (e.g. "A", "AA", "AAA")
        else:
            if n == 1: # Columns always start from 'A'
                return "INVALID_LEFT_CELL"

            new_column_part = 'Z' * (n - 1) # Reconstruct with new column
            return f"{new_column_part}{row_part}"

        # Join the characters back to form the new column part
        new_column_part = "".join(chars)

        return f"{new_column_part}{row_part}"

    def get_below_cell_name(self,
                            name: str,
                            ) ->  str:
        """"""
        match = re.match(r"([A-Z]+)(\d+)", name, re.IGNORECASE)

        column_part = match.group(1).upper()
        row_part_str = match.group(2)

        try:
            row_number = int(row_part_str)
            new_row_number = row_number + 1
            return f"{column_part}{new_row_number}"

        except ValueError:
            return "INVALID_BELOW_NUMBER"

    def get_column_name_from_column(self,
                                    column: int = 0,
                                    ) ->    str:
        """"""
        if column == 0:
            return 'A'

        column -= 1

        name = ''
        while column >= 0:
            name = chr(65 + column % 26) + name
            column //= 26
            column -= 1

        return name

    def get_cell_name_from_position(self,
                                    column: int = 0,
                                    row:    int = 0,
                                    ) ->    str:
        """"""
        column_name = self.get_column_name_from_column(column)
        row_name = str(row) if row >= 0 else ''
        return column_name + row_name

    def get_cell_position_from_name(self,
                                    name: str,
                                    ) ->  tuple[int, int]:
        """
        Parses a cell name into a (column, row) tuple.

        Returns None if the name cannot be parsed into a valid position.
        """
        cell_part_pattern = r"([A-Za-z]+\d*|[A-Za-z]*\d+)"
        match = re.match(cell_part_pattern, name, re.IGNORECASE)

        if not match:
            return None

        cell_part = match.group(1)
        col = 0 # Default for column index
        row = 0 # Default for row index

        # Check the composition of the cell_part
        has_letters = bool(re.search(r"[A-Za-z]", cell_part))
        has_digits = bool(re.search(r"\d", cell_part))

        if has_letters and has_digits:
            # Case 1: Contains both letters and digits (e.g. 'A10', 'AA5', 'ABC123')
            # This is a standard column-row reference.
            col_letters_match = re.search(r"([A-Za-z]+)", cell_part)
            row_str_match = re.search(r"(\d+)", cell_part)

            if not (col_letters_match and row_str_match):
                return None

            col_letters = col_letters_match.group(1)
            row_str = row_str_match.group(1)

            # Convert column letters to 1-based index
            for c in col_letters.upper():
                col = col * 26 + (ord(c) - ord('A') + 1)
            # Convert row string to 1-based integer
            row = int(row_str)

        elif has_digits:
            # Case 2: Contains only digits (e.g. '5', '10')
            # This implies a specific row with column 0.
            col = 0 # Explicitly set column to 0
            row = int(cell_part) # Row is the number itself (1-based)

        elif has_letters:
            # Case 3: Contains only letters (e.g. 'h', 'H', 'HIJ')
            # This implies a specific column with row 0.
            # Convert column letters to 1-based index
            for c in cell_part.upper():
                col = col * 26 + (ord(c) - ord('A') + 1)
            row = 0 # Explicitly set row to 0

        else:
            return None

        # Basic validation for sensible results (col/row shouldn't be negative).
        # A (0, 0) result is valid but is not possible to achieve from the input bar.
        if col < 0 and row < 0:
            return None

        return (col, row)

    def get_cell_range_from_name(self,
                                 name: str,
                                 ) ->  tuple[int, int, int, int]:
        """
        Parses a cell range (e.g. 'A10:A20', 'AA5:BB20', '5:10', 'H:H')
        or a single cell (e.g. 'A10', '123', 'HIJ', 'ABC123') into a tuple
        of (start_col, start_row, end_col, end_row).

        Returns (-1, -1, -1, -1) if the name cannot be parsed.
        """
        cell_part_pattern = r"([A-Za-z]*\d*|[A-Za-z]*\d*)"
        pattern = fr"{cell_part_pattern}(:{cell_part_pattern})?"
        match = re.match(pattern, name, re.IGNORECASE)

        if not match:
            return (-1, -1, -1, -1)

        start_name_part = match.group(1)
        end_name_part = match.group(3)

        start_pos = self.get_cell_position_from_name(start_name_part)

        if start_pos is None:
            return (-1, -1, -1, -1)

        if end_name_part: # If a second part exists (it's a range)
            end_pos = self.get_cell_position_from_name(end_name_part)
            if end_pos is None:
                return (-1, -1, -1, -1)
            return (*start_pos, *end_pos)
        else: # It's a single cell name
            return (*start_pos, *start_pos)

    def check_cell_position_near_edges(self,
                                       column:          int,
                                       row:             int,
                                       viewport_height: int,
                                       viewport_width:  int,
                                       ) ->             list[str]:
        """"""
        cell_y = self.get_cell_y_from_row(row)
        cell_x = self.get_cell_x_from_column(column)
        cell_width  = self.get_cell_width_from_column(column)
        cell_height = self.get_cell_height_from_row(row)

        x_offset = self.left_locator_width - self.scroll_x_position
        y_offset = self.top_locator_height - self.scroll_y_position

        top_offset  = cell_y - y_offset
        left_offset = cell_x - x_offset

        top_limit  = top_offset  - (viewport_height - (viewport_height % self.DEFAULT_CELL_HEIGHT)) + cell_height
        left_limit = left_offset - (viewport_width  - (viewport_width  % self.DEFAULT_CELL_WIDTH))  + cell_width

        near_edges = []

        # Check if the target cell is near the bottom of the viewport
        if abs(self.scroll_y_position - top_limit) <= self.DEFAULT_CELL_HEIGHT:
            near_edges.append('bottom')

        # Check if the target cell is near the top of the viewport
        if abs(self.scroll_y_position - top_offset) <= self.DEFAULT_CELL_HEIGHT:
            near_edges.append('top')

        # Check if the target cell is near the right of the viewport
        if abs(self.scroll_x_position - left_limit) <= self.DEFAULT_CELL_WIDTH:
            near_edges.append('right')

        # Check if the target cell is near the left of the viewport
        if abs(self.scroll_x_position - left_offset) <= self.DEFAULT_CELL_WIDTH:
            near_edges.append('left')

        return near_edges

    def scroll_to_position(self,
                           column:          int,
                           row:             int,
                           viewport_height: int,
                           viewport_width:  int,
                           scroll_axis:     str = 'both',
                           ) ->             bool:
        """"""
        cell_y = self.get_cell_y_from_row(row)
        cell_x = self.get_cell_x_from_column(column)
        cell_width  = self.get_cell_width_from_column(column)
        cell_height = self.get_cell_height_from_row(row)

        x_offset = self.left_locator_width - self.scroll_x_position
        y_offset = self.top_locator_height - self.scroll_y_position

        bottom_offset = cell_y + cell_height - y_offset
        top_offset    = cell_y - y_offset
        right_offset  = cell_x + cell_width - x_offset
        left_offset   = cell_x - x_offset

        # Skip if the target cell is already visible
        if (
            self.scroll_y_position <= top_offset                               and \
            bottom_offset          <= self.scroll_y_position + viewport_height and \
            self.scroll_x_position <= left_offset                              and \
            right_offset           <= self.scroll_x_position + viewport_width
        ):
            return False

        # Scroll down when the target cell is below the viewport so that the target cell is near the bottom
        # of the viewport
        if scroll_axis in {'both', 'vertical'} and bottom_offset > self.scroll_y_position + viewport_height:
            self.scroll_y_position = top_offset - viewport_height + cell_height

        # Scroll up when the target cell is above the viewport so that the target cell is exactly at the top
        # of the viewport
        if scroll_axis in {'both', 'vertical'} and top_offset < self.scroll_y_position:
            self.scroll_y_position = top_offset

        # Scroll to the right when the target cell is to the right of the viewport so that the target cell
        # is near the right of the viewport
        if scroll_axis in {'both', 'horizontal'} and right_offset > self.scroll_x_position + viewport_width:
            self.scroll_x_position = left_offset - viewport_width + cell_width

        # Scroll to the left when the target cell is to the left of the viewport so that the target cell
        # is exactly at the left of the viewport
        if scroll_axis in {'both', 'horizontal'} and left_offset < self.scroll_x_position:
            self.scroll_x_position = left_offset

        self.scroll_y_position = max(0, self.scroll_y_position)
        self.scroll_x_position = max(0, self.scroll_x_position)

        return True
