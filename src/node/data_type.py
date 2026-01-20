# data_type.py
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
from typing import Any
from typing import TypeAlias

Row:        TypeAlias = int
Column:     TypeAlias = int
Coordinate: TypeAlias = tuple[Row, Column]
Tables:     TypeAlias = tuple[Coordinate, DataFrame]
Sparse:     TypeAlias = dict[Coordinate, Any]

class Sheet():

    tables: Tables = []
    sparse: Sparse = {}
