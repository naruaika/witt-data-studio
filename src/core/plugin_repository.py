# plugin_repository.py
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

from polars import Expr
from polars.api import register_expr_namespace

try:
    import witt_strutil as strx

    @register_expr_namespace('strx')
    class ExpandedStringExpr:

        def __init__(self,
                     expr: Expr,
                     ) ->  None:
            """"""
            self._expr = expr

        def pig_latinnify(self) -> Expr:
            """"""
            return strx.pig_latinnify(self._expr)

        def split_by_chars(self,
                           characters: str,
                           ) ->        Expr:
            """"""
            return strx.split_by_chars(self._expr, characters)

        def split_by_lowercase_to_uppercase(self) -> Expr:
            """"""
            return strx.split_by_lowercase_to_uppercase(self._expr)

        def split_by_uppercase_to_lowercase(self) -> Expr:
            """"""
            return strx.split_by_uppercase_to_lowercase(self._expr)

        def to_sentence_case(self) -> Expr:
            """"""
            return strx.to_sentence_case(self._expr)

        def to_sponge_case(self) -> Expr:
            """"""
            return strx.to_sponge_case(self._expr)

except ModuleNotFoundError:
    pass