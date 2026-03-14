# table_filter.py
#
# Copyright 2025 Naufan Rusyda Faikar <hello@naruaika.me>
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

from gi.repository import Gtk
from polars import DataType

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
