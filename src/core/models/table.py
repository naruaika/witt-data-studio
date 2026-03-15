# table.py
#
# Copyright (c) 2025 Naufan Rusyda Faikar <hello@naruaika.me>
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
                 tname:         str,
                 content:       DataFrame,
                 with_header:   bool,
                 bounding_box:  BoundingBox,
                 placeholder:   bool  = False,
                 query_plan:    bytes = None,
                 error_message: str   = None,
                 ) ->           None:
        """"""
        super().__init__(content)

        self.content       = content
        self.tname         = tname
        self.with_header   = with_header
        self.bounding_box  = bounding_box
        self.placeholder   = placeholder
        self.query_plan    = query_plan
        self.error_message = error_message
