# utils_polars.py
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

from polars import DataType
from typing import Any

def cast_dtype(value: str,
               dtype: DataType) -> Any:
    """"""
    from datetime import datetime
    from polars import Date
    from polars import Datetime
    from polars import Series
    from polars import Time

    if isinstance(dtype, Datetime):
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    if isinstance(dtype, Date):
        return datetime.strptime(value, '%Y-%m-%d').date()
    if isinstance(dtype, Time):
        return datetime.strptime(value, '%H:%M:%S').time()

    try:
        return Series([value]).cast(dtype)[0]
    except Exception:
        return str(value)
