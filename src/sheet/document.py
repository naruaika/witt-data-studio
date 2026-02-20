# document.py
#
# Copyright (c) 2025 Naufan Rusyda Faikar
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

from enum import Enum
from polars import DataFrame
from polars import LazyFrame
from polars import Series
from typing import Any
from typing import TypeAlias
import asyncio

from ..core.document import Document
from ..core.datatable import BoundingBox
from ..core.datatable import DataTable
from ..core.utils import cast_dtype
from ..core.utils import get_dtype
from ..core.utils import infer_dtype
from ..core.utils import unique_name

from .canvas import SheetCanvas
from .display import SheetDisplay
from .widget import SheetTableFilter

Row:        TypeAlias = int
Column:     TypeAlias = int
Coordinate: TypeAlias = tuple[Row, Column]
Tables:     TypeAlias = list[DataTable]
Sparse:     TypeAlias = dict[Coordinate, Any]

class SheetOperation(Enum):

    CREATE_TABLE         = 1
    UPDATE_TABLE         = 2
    UPDATE_TABLE_HEADER  = 3
    UPDATE_TABLE_CONTENT = 4
    UPDATE_TABLE_CELL    = 5
    UPDATE_TABLE_RANGE   = 6
    UPDATE_TABLE_COLUMNS = 7
    UPDATE_TABLE_ROWS    = 8
    DELETE_TABLE         = 9
    DELETE_TABLE_COLUMNS = 10
    DELETE_TABLE_ROWS    = 11
    INSERT_SPARSE        = 12
    UPDATE_SPARSE        = 13
    DELETE_SPARSE        = 14
    DO_NOTHING           = 15



class SheetDocument(Document):

    def __init__(self,
                 Canvas:  SheetCanvas,
                 display: SheetDisplay
                 ) ->     None:
        """"""
        super().__init__(title = _('Sheet'))

        self.Canvas  = Canvas
        self.display = display

        self.tables  = []
        self.sparse  = {}
        self.widgets = {}

        # I don't think the implementation of document'
        # bounding box is useful enough to improve the
        # rendering performance. Maybe this is an early
        # optimization crime after all. Anyway, it does
        # a good job in theory, because it is stupid to
        # iterate over out of bound document data area.
        # Well, what if the user does dirty action like
        # having data positioned far away from the rest
        # that will make this meaningless? Flag this as
        # TODO for now.
        self.bounding_box = BoundingBox()

        if self.has_data():
            self._update_bounding_box()

    def has_data(self) -> bool:
        """"""
        return len(self.tables) + len(self.sparse) > 0

    def read_data(self,
                  column:     int,
                  row:        int,
                  with_dtype: bool = False,
                  ) ->        Any:
        """"""
        table = self.get_table_by_position(column, row)

        if not isinstance(table, DataTable):
            if content := self.sparse.get((row, column)):
                if with_dtype:
                    dtype = get_dtype(content)
                    return content, dtype
                return content

            if with_dtype:
                return None, ''
            return None

        bbox = table.bounding_box

        # Transform to 0-based
        column -= bbox.column
        row -= bbox.row

        if with_dtype:
            column_name = table.columns[column]
            dtype = table.schema[column_name]
            dtype = str(dtype.__class__.__name__)
            if dtype == 'String':
                dtype = 'Text'

        if table.with_header:
            if row == 0:
                content = table.columns[column]
                if with_dtype:
                    return content, dtype
                return content
            row -= 1

        content = table[row, column]
        if with_dtype:
            return content, dtype
        return content

    def update_data(self,
                    content: Any,
                    column:  int,
                    row:     int,
                    ) ->     SheetOperation:
        """"""
        table = self.get_table_by_position(column, row)
        if isinstance(table, DataTable):
            return self.update_table_data(content, table, column, row)
        return self.create_or_update_sparse(content, column, row)

    def create_table(self,
                     content:     Any,
                     with_header: bool,
                     column:      int      = 1,
                     row:         int      = 1,
                     table_name:  str      = '',
                     prefer_sync: bool     = False,
                     on_finish:   callable = None,
                     ) ->         int:
        """"""
        is_lazyframe = isinstance(content, LazyFrame)

        if is_lazyframe:
            if prefer_sync:
                content = content.collect()
            else:
                to_load = content
                content = DataFrame({'#LOADING!': None}).head(0)

        if not isinstance(content, DataFrame):
            from io import BytesIO
            from polars import read_csv
            content_str = str(content).encode('utf-8')
            content_bytes = BytesIO(content_str)
            # We don't infer schema for non-tabular content,
            # meaning that all cell data are and will always
            # be stored as string.
            try:
                content = read_csv(content_bytes,
                                   separator    = '\t',
                                   has_header   = True,
                                   infer_schema = True)
            except Exception:
                # Retry by ignoring any errors
                content = read_csv(content_bytes,
                                   separator     = '\t',
                                   has_header    = True,
                                   ignore_errors = True,
                                   infer_schema  = False)
            with_header = True

        column_span = content.width
        row_span = content.height
        row_span += 1 if with_header else 0
        bounding_box = BoundingBox(column, row, column_span, row_span)

        table_names = [table.tname for table in self.tables]
        new_name = unique_name(_('Table'), table_names, table_name)

        new_table = DataTable(tname        = new_name,
                              content      = content,
                              with_header  = with_header,
                              bounding_box = bounding_box,
                              placeholder  = is_lazyframe)

        self.tables.append(new_table)

        for tindex, table in enumerate(self.tables):
            if table is new_table:
                break

        self._update_bounding_box(bounding_box)

        if not is_lazyframe:
            self.repopulate_table_widgets()

        async def do_load(old_table: DataTable,
                          lazyframe: LazyFrame,
                          ) ->       None:
            """"""
            error_message = None

            try:
                dataframe = await lazyframe.collect_async()
            except Exception as e:
                dataframe = DataFrame({'#ERROR!': None}).head(0)
                error_message = str(e)

            for tindex, table in enumerate(self.tables):
                if table is old_table:
                    self.replace_table(dataframe, tindex)
                    table = self.tables[tindex]
                    if error_message:
                        table.placeholder = True
                        table.error_message = error_message
                    else:
                        table.query_plan = lazyframe.serialize()
                    on_finish(table)
                    break

        if is_lazyframe and not prefer_sync:
            coroutine = do_load(new_table, to_load)
            asyncio.create_task(coroutine)

        return tindex

    def replace_table(self,
                      dataframe:   DataFrame,
                      table_index: int,
                      ) ->         SheetOperation:
        """"""
        try:
            table = self.tables[table_index]
        except:
            return SheetOperation.DO_NOTHING

        column = table.bounding_box.column
        row = table.bounding_box.row
        column_span = dataframe.width
        row_span = dataframe.height
        row_span += 1 if table.with_header else 0
        bounding_box = BoundingBox(column, row, column_span, row_span)

        self.tables[table_index] = DataTable(table.tname,
                                             dataframe,
                                             table.with_header,
                                             bounding_box)

        n_col_changed = dataframe.width != table.width
        n_row_changed = dataframe.height != table.height

        if n_col_changed or n_row_changed:
            self._update_bounding_box(to_shrink = True)

        self.repopulate_table_widgets()

        return SheetOperation.UPDATE_TABLE

    def update_table_data(self,
                          content: Any,
                          table:   DataTable,
                          column:  int,
                          row:     int,
                          ) ->     SheetOperation:
        """"""
        # Convert to 0-based
        column = column - table.bounding_box.column
        row = row - table.bounding_box.row

        if table.with_header:
            row = row - 1

        # Update header instead of content
        if row == -1:
            old_name = table.columns[column]

            if old_name == content:
                return

            tidx = self.get_table_index_by_name(table.tname)
            new_name = unique_name(_('column'),
                                   table.columns,
                                   new_name  = content,
                                   old_name  = old_name,
                                   separator = '_')
            dataframe = table.rename({old_name: new_name})
            self.tables[tidx] = DataTable(table.tname,
                                          dataframe,
                                          table.with_header,
                                          table.bounding_box)

            return SheetOperation.UPDATE_TABLE_HEADER

        from polars import List
        from polars import Object
        from polars import Struct

        dtype = table.dtypes[column]

        if isinstance(dtype, (List, Object, Struct)):
            return SheetOperation.DO_NOTHING
            # we don't support updating an object

        # Convert the input value to the correct type
        content = cast_dtype(content, dtype)

        # Cast empty string
        if content == '':
            content = None

        table[row, column] = content

        return SheetOperation.UPDATE_TABLE_CONTENT

    def update_table_column(self,
                            series:      Series,
                            table_index: int,
                            column_name: str,
                            ) ->         SheetOperation:
        """"""
        try:
            table = self.tables[table_index]
        except:
            return SheetOperation.DO_NOTHING

        if column_name not in table.columns:
            return SheetOperation.DO_NOTHING

        new_column = column_name != series.name
        index = table.columns.index(column_name)

        try:
            if new_column:
                dataframe = self.tables[table_index].insert_column(index+1, series)
            else:
                dataframe = self.tables[table_index].with_columns(series)
        except:
            return SheetOperation.DO_NOTHING

        if new_column:
            table.bounding_box.column_span += 1

        self.tables[table_index] = DataTable(table.tname,
                                             dataframe,
                                             table.with_header,
                                             table.bounding_box)

        if new_column:
            self._update_bounding_box(table.bounding_box)

        return SheetOperation.UPDATE_TABLE_CONTENT

    def delete_table(self,
                     table_index: int,
                     ) ->         SheetOperation:
        """"""
        try:
            del self.tables[table_index]
        except:
            return SheetOperation.DO_NOTHING

        self._update_bounding_box(to_shrink = True)

        return SheetOperation.DELETE_TABLE

    def delete_table_column(self,
                            table_index: int,
                            column_name: str,
                            ) ->         SheetOperation:
        """"""
        try:
            table = self.tables[table_index]
        except:
            return SheetOperation.DO_NOTHING

        if column_name not in table.columns:
            return SheetOperation.DO_NOTHING

        from polars import all
        dataframe = table.select(all().exclude(column_name))

        return self.replace_table(dataframe, table_index)

    def create_or_update_sparse(self,
                                content: Any,
                                column:  int,
                                row:     int,
                                ) ->     SheetOperation:
        """"""
        key_exists = (row, column) in self.sparse

        if content is not None:
            content = infer_dtype(content)
            self.sparse[(row, column)] = content
            bounding_box = BoundingBox(column, row, 1, 1)

            self._update_bounding_box(bounding_box)

            return SheetOperation.INSERT_SPARSE \
                   if not key_exists \
                   else SheetOperation.UPDATE_SPARSE

        if key_exists:
            del self.sparse[(row, column)]
            self._update_bounding_box(to_shrink = True)
            return SheetOperation.DELETE_SPARSE

        return SheetOperation.DO_NOTHING

    def get_table_by_name(self,
                          name: str,
                          ) ->  DataTable:
        """"""
        for table in reversed(self.tables):
            if table.tname == name:
                return table
        return None

    def get_table_by_position(self,
                              column: int,
                              row:    int,
                              ) ->    DataTable:
        """"""
        for table in reversed(self.tables):
            if table.bounding_box.contains(column, row):
                return table
        return None

    def get_table_column_by_position(self,
                                     column: int,
                                     row:    int,
                                     ) ->    tuple[DataTable, str]:
        """"""
        table = self.get_table_by_position(column, row)

        if not isinstance(table, DataTable):
            return None, None

        # Transform to 0-based
        bbox = table.bounding_box
        column -= bbox.column

        column_name = table.columns[column]

        return table, column_name

    def get_table_index_by_name(self,
                                table_name: str,
                                ) ->        int:
        """"""
        for tidx, table in enumerate(self.tables):
            if table.tname == table_name:
                return tidx
        return None

    def get_intersect_tables(self,
                             column:      int,
                             row:         int,
                             column_span: int,
                             row_span:    int,
                             ) ->         list[DataTable]:
        """"""
        target = BoundingBox(column, row, column_span, row_span)
        tables = []
        for table in self.tables:
            if table.bounding_box.intersects(target):
                tables.append(table)
        return tables

    def repopulate_table_widgets(self) -> None:
        """"""
        if 'table' not in self.widgets:
            self.widgets['table'] = []

        widgets = self.widgets['table']

        while widgets:
            widgets[0].unparent()
            del widgets[0]

        for table in self.tables:
            if table.height == 0:
                continue
            bbox = table.bounding_box
            y = self.display.get_cell_y_from_row(bbox.row)
            for column_index in range(table.width):
                column = bbox.column + column_index
                column = self.display.get_column_from_lcolumn(column)
                if column < 0:
                    continue # skip if the column is hidden
                widget = SheetTableFilter(0, 0, column, bbox.row)
                x = self.display.get_cell_x_from_column(column)
                x = x + self.display.get_cell_width_from_column(column)
                x = x - widget.WIDTH
                widget.x = x
                widget.y = y
                widgets.append(widget)
                self.Canvas.add_overlay(widget)

    def reposition_table_widgets(self) -> None:
        """"""
        if 'table' not in self.widgets:
            self.widgets['table'] = []
            return

        widgets = self.widgets['table']

        widget_index = 0
        for table in self.tables:
            if table.width <= 1 and table.height == 0:
                continue
            bbox = table.bounding_box
            y = self.display.get_cell_y_from_row(bbox.row)
            for column_index in range(table.width):
                column = bbox.column + column_index
                column = self.display.get_column_from_lcolumn(column)
                if column < 0:
                    continue # skip if it's hidden
                try:
                    widget = widgets[widget_index]
                except:
                    break # shouldn't happen at all
                x = self.display.get_cell_x_from_column(column)
                x = x + self.display.get_cell_width_from_column(column)
                x = x - widget.WIDTH
                widget.x = x
                widget.y = y
                widget_index += 1

        self.Canvas.queue_allocate()

    def _update_bounding_box(self,
                             in_bbox:   BoundingBox = None,
                             to_shrink: bool        = False,
                             ) ->       None:
        """"""
        column      = 0 if to_shrink else self.bounding_box.column
        row         = 0 if to_shrink else self.bounding_box.row
        column_span = 0 if to_shrink else self.bounding_box.column_span
        row_span    = 0 if to_shrink else self.bounding_box.row_span

        # Check if the existing bounding box is initialized,
        # otherwise we need to calculate it from ground up.
        initialized = column > 0 and row > 0

        if initialized and in_bbox:
            end_column = column + column_span
            end_column = max(end_column, in_bbox.column + in_bbox.column_span)

            end_row = row + row_span
            end_row = max(end_row, in_bbox.row + in_bbox.row_span)

            column      = min(column, in_bbox.column)
            row         = min(row, in_bbox.row)
            column_span = end_column - column
            row_span    = end_row - row

            # Update the bounding box
            self.bounding_box.column      = column
            self.bounding_box.row         = row
            self.bounding_box.column_span = column_span
            self.bounding_box.row_span    = row_span
            return

        for tidx, table in enumerate(self.tables):
            bbox = table.bounding_box

            in_column      = bbox.column
            in_row         = bbox.row
            in_column_span = bbox.column_span
            in_row_span    = bbox.row_span

            # Initialize the bounding box
            if tidx == 0:
                column      = in_column
                row         = in_row
                column_span = in_column_span
                row_span    = in_row_span
                initialized = True
                continue

            in_end_column = in_column + in_column_span
            in_end_row = in_row + in_row_span

            end_column = column + column_span
            end_row = row + row_span

            column      = min(column, in_column)
            row         = min(row, in_row)
            column_span = max(end_column, in_end_column) - column
            row_span    = max(end_row, in_end_row) - row

        coordinates = self.sparse.keys()
        for sidx, coordinate in enumerate(coordinates):
            in_row, in_column = coordinate
            should_initialize = sidx == 0 and \
                                not initialized

            # Initialize the bounding box
            if should_initialize:
                column      = in_column
                row         = in_row
                column_span = 1
                row_span    = 1
                continue

            end_column = column + column_span
            end_column = max(end_column, in_column + 1)

            end_row = row + row_span
            end_row = max(end_row, in_row + 1)

            column      = min(column, in_column)
            row         = min(row, in_row)
            column_span = end_column - column
            row_span    = end_row - row

        # Update the bounding box
        self.bounding_box.column      = column
        self.bounding_box.row         = row
        self.bounding_box.column_span = column_span
        self.bounding_box.row_span    = row_span
