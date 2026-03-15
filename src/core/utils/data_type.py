# data_type.py
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

from datetime import datetime
from datetime import date
from datetime import time
from decimal  import Decimal
from typing   import Any

def get_dtype(value: Any) -> str:
    """"""
    if isinstance(value, str):
        return 'Text'
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
    from .numeric import cast_numeric
    value = cast_numeric(value)
    if not isinstance(value, str):
        return value

    # Try to cast to datetime or date
    from .temporal import get_date_format_string
    if fmt := get_date_format_string(value):
        if '%H' in fmt or '%I' in fmt:
            return datetime.strptime(value, fmt)
        return datetime.strptime(value, fmt).date()

    # Try to cast to time
    from .temporal import get_time_format_string
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
    from .temporal import get_date_format_string
    if string and (fmt := get_date_format_string(string)):
        return datetime.strptime(string, fmt)
    return string


def todate(string: str) -> date:
    """"""
    from .temporal import get_date_format_string
    if string and (fmt := get_date_format_string(string)):
        return datetime.strptime(string, fmt).date()
    return string


def totime(string: str) -> time:
    """"""
    from .temporal import get_time_format_string
    if string and (fmt := get_time_format_string(string)):
        return datetime.strptime(string, fmt).time()
    return string
