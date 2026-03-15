# numeric.py
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

from decimal import Decimal
from typing import Any

def cast_numeric(value: str) -> Any:
    """"""
    if not isinstance(value, str):
        return value

    if value in {'', None}:
        return None

    if '.' not in value:
        try:
            return int(value)
        except Exception:
            pass

    try:
        return Decimal(value)
    except Exception:
        pass

    # I don't know, but it seems like there's no case
    # where Decimal() cannot capture but float() can.
    try:
        return float(value)
    except Exception:
        pass

    return value
