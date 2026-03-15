# temporal.py
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

from datetime import timedelta

# A comprehensive list of common date formats. Order can be important for
# performance and ambiguity resolution; more specific formats should be
# listed before more general ones.
COMMON_DATE_FORMATS = [
    '%Y-%m-%d %H:%M:%S',  # 2025-01-15 10:30:00
    '%Y-%m-%dT%H:%M:%S',  # 2025-01-15T10:30:00
    '%Y/%m/%d %H:%M:%S',  # 2025/01/15 10:30:00
    '%m/%d/%Y %H:%M:%S',  # 01/15/2025 10:30:00
    '%d/%m/%Y %H:%M:%S',  # 15/01/2025 10:30:00
    '%b %d, %Y %I:%M %p', # Jan 15, 2025 10:30 AM
    '%B %d, %Y %I:%M %p', # January 15, 2025 10:30 AM
    '%Y-%m-%d',           # 2025-01-15
    '%m/%d/%Y',           # 01/15/2025
    '%d/%m/%Y',           # 15/01/2025
    '%B %d, %Y',          # January 15, 2021
    '%b %d, %Y',          # Jan 15, 2021
    '%d-%b-%Y',           # 15-Jan-2025
    '%d %B %Y',           # 15 January 2025
    '%Y%m%d',             # 20250115
    '%Y',                 # 2025
    '%Y-%m',              # 2025-01
    '%m-%Y',              # 01-2025
    '%m/%Y',              # 01/2025
    '%b %Y',              # Jan 2025
    '%b-%Y',              # Jan-2025
    '%B %Y',              # January 2025
#   '%m-%d',              # 01-15
#   '%m/%d',              # 01/15
#   '%d/%m',              # 15/01
#   '%B %d,',             # January 15
#   '%b %d,',             # Jan 15
#   '%d-%b',              # 15-Jan
#   '%d %B',              # 15 January
]


COMMON_TIME_FORMATS = [
    '%H:%M:%S',           # 10:30:00
    '%I:%M %p',           # 10:30 AM
    '%H:%M',              # 10:30
]


def istemporal(date_string: str) -> bool:
    """"""
    from datetime import datetime
    from datetime import date
    from datetime import time
    if isinstance(date_string, (date, time, datetime)):
        return True

    from dateutil import parser
    if not isinstance(date_string, str):
        date_string = str(date_string)
    try:
        parser.parse(date_string)
        return True
    except Exception:
        return False


def get_date_format_string(date_string: str) -> str:
    """"""
    from dateutil import parser
    from datetime import datetime

    if isinstance(date_string, int):
        return None

    if date_string in {'', None}:
        return None

    if not isinstance(date_string, str):
        date_string = str(date_string)

    try:
        # We'll use the result of the dateutil parsing as
        # a reference due to its robustness.
        parsed_date_1 = parser.parse(date_string)
    except Exception:
        return None

    for date_format in COMMON_DATE_FORMATS:
        try:
            parsed_date_2 = datetime.strptime(date_string, date_format)
            if parsed_date_1 == parsed_date_2:
                return date_format
        except Exception:
            continue

    return None


def get_time_format_string(date_string: str) -> str:
    """"""
    from dateutil import parser
    from datetime import datetime

    if isinstance(date_string, int):
        return None

    if date_string in {'', None}:
        return None

    if not isinstance(date_string, str):
        date_string = str(date_string)

    try:
        # We'll use the result of the dateutil parsing as
        # a reference due to its robustness.
        parsed_date_1 = parser.parse(date_string)
    except Exception:
        return None

    for date_format in COMMON_TIME_FORMATS:
        try:
            parsed_date_2 = datetime.strptime(date_string, date_format)
            equal_hour = parsed_date_1.hour == parsed_date_2.hour
            equal_minute = parsed_date_1.minute == parsed_date_2.minute
            if equal_hour and equal_minute:
                return date_format
        except Exception:
            continue

    return None


def print_timedelta(td: timedelta) -> str:
        """"""
        days = td.days
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        microseconds = td.microseconds

        parts = []
        if days:
            parts.append(f'{days}d')
        if hours:
            parts.append(f'{hours}h')
        if minutes:
            parts.append(f'{minutes}m')
        if seconds:
            parts.append(f'{seconds}s')
        if microseconds:
            parts.append(f'{microseconds}µs')

        return ' '.join(parts) if parts else '0µs'
