# utils_type.py
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

from datetime import datetime
from datetime import date
from datetime import time
from decimal import Decimal
from typing import Any

def get_dtype(value: Any) -> str:
    """"""
    if isinstance(value, str):
        return 'String'
    if isinstance(value, int):
        return 'Int'
    if isinstance(value, float):
        return 'Float'
    if isinstance(value, Decimal):
        return 'Decimal'
    if isinstance(value, date):
        return 'Date'
    if isinstance(value, time):
        return 'Time'
    if isinstance(value, datetime):
        return 'Datetime'
    return 'Object'


def infer_dtype(value: str) -> Any:
    """"""
    if not isinstance(value, str):
        return value

    # Try to cast to boolean
    if value.lower() in {'true', 'false'}:
        return True if value.lower() == 'true' \
                    else False

    # Try to cast to numeric
    from .utils_numeric import cast_numeric
    value = cast_numeric(value)
    if not isinstance(value, str):
        return value

    # Try to cast to datetime or date
    from .utils_temporal import get_date_format_string
    if fmt := get_date_format_string(value):
        if '%H' in fmt or '%I' in fmt:
            return datetime.strptime(value, fmt)
        return datetime.strptime(value, fmt).date()

    # Try to cast to time
    from .utils_temporal import get_time_format_string
    if fmt := get_time_format_string(value):
        return datetime.strptime(value, fmt).time()

    return value


def isiterable(obj: Any) -> bool:
    """"""
    from collections.abc import Sequence
    return isinstance(obj, Sequence) and \
           not isinstance(obj, (str, bytes, bytearray))


def toboolean(string: str) -> bool:
    """"""
    if string.lower() in {'true', 'yes', '1'}:
        return True
    return False


def todatetime(string: str) -> datetime:
    """"""
    from .utils_temporal import get_date_format_string
    if string and (fmt := get_date_format_string(string)):
        return datetime.strptime(string, fmt)
    return string


def todate(string: str) -> date:
    """"""
    from .utils_temporal import get_date_format_string
    if string and (fmt := get_date_format_string(string)):
        return datetime.strptime(string, fmt).date()
    return string


def totime(string: str) -> time:
    """"""
    from .utils_temporal import get_time_format_string
    if string and (fmt := get_time_format_string(string)):
        return datetime.strptime(string, fmt).time()
    return string
