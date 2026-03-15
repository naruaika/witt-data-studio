# table_filter.py
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

from gi.repository import Gtk
from polars        import DataType

class SheetColumnDType(Gtk.Image):

    __gtype_name__ = 'SheetColumnDType'

    WIDTH  = 22 + 8
    HEIGHT = 22 + 2

    x = 0
    y = 0

    def __init__(self,
                 x:      int,
                 y:      int,
                 column: int,
                 row:    int,
                 dtype:  DataType,
                 ) ->    None:
        """"""
        from polars import Boolean
        from polars import Categorical
        from polars import Date
        from polars import Datetime
        from polars import Duration
        from polars import String
        from polars import Time

        icon_name = 'xxx-object-symbolic'
        if dtype.is_(String):
            icon_name = 'xxx-character-upper-case-symbolic'
        if dtype.is_(Boolean):
            icon_name = 'xxx-boolean-symbolic'
        if dtype.is_numeric():
            icon_name = 'xxx-character-whole-number-symbolic'
        if isinstance(dtype, Categorical):
            icon_name = 'xxx-tag-symbolic'
        if isinstance(dtype, (Date, Datetime)):
            icon_name = 'xxx-calendar-symbolic'
        if isinstance(dtype, Time):
            icon_name = 'xxx-time-symbolic'
        if isinstance(dtype, Duration):
            icon_name = 'xxx-hourglass-symbolic'

        super().__init__(icon_name = icon_name)

        self.set_size_request(self.WIDTH, self.HEIGHT)

        self.x = x
        self.y = y

        self.column = column
        self.row    = row
