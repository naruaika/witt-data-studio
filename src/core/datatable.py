# datatable.py
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

from polars import DataFrame

class BoundingBox():

    def __init__(self,
                 column:      int = 0,
                 row:         int = 0,
                 column_span: int = 0,
                 row_span:    int = 0,
                 ) ->         None:
        """"""
        self.column      = column
        self.row         = row
        self.column_span = column_span
        self.row_span    = row_span

    @property
    def right(self) -> int:
        """"""
        return self.column + self.column_span

    @property
    def bottom(self) -> int:
        """"""
        return self.row + self.row_span

    def contains(self,
                 column: int,
                 row:    int,
                 ) ->    bool:
        """"""
        return self.column <= column <= self.column + self.column_span - 1 and \
               self.row    <= row    <= self.row    + self.row_span    - 1

    def intersects(self,
                   target: 'BoundingBox',
                   ) ->    'bool':
        """"""
        is_disjoint = (
            self.right  <= target.column or # left of target
            self.column >= target.right  or # right of target
            self.bottom <= target.row    or # above target
            self.row    >= target.bottom    # below target
        )
        return not is_disjoint



class DataTable(DataFrame):

    def __init__(self,
                 tname:        str,
                 content:      DataFrame,
                 with_header:  bool,
                 bounding_box: BoundingBox,
                 placeholder:  bool = False,
                 ) ->          None:
        """"""
        super().__init__(content)

        self.tname        = tname
        self.with_header  = with_header
        self.bounding_box = bounding_box
        self.placeholder  = placeholder
