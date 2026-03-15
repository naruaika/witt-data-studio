# polars.py
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

from polars import DataType
from typing import Any

def cast_dtype(value: str,
               dtype: DataType,
               ) ->   Any:
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
