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
from warnings import deprecated

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

        def split_by_character_transition(self,
                                          before: list[str],
                                          after:  list[str],
                                          ) ->    Expr:
            """"""
            return strx.split_by_character_transition(self._expr, before, after)

        @deprecated('Use split_by_character_transition instead')
        def split_by_lowercase_to_uppercase(self) -> Expr:
            """"""
            return strx.split_by_lowercase_to_uppercase(self._expr)

        @deprecated('Use split_by_character_transition instead')
        def split_by_uppercase_to_lowercase(self) -> Expr:
            """"""
            return strx.split_by_uppercase_to_lowercase(self._expr)

        @deprecated('Use split_by_character_transition instead')
        def split_by_digit_to_nondigit(self) -> Expr:
            """"""
            return strx.split_by_digit_to_nondigit(self._expr)

        @deprecated('Use split_by_character_transition instead')
        def split_by_nondigit_to_digit(self) -> Expr:
            """"""
            return strx.split_by_nondigit_to_digit(self._expr)

        def to_sentence_case(self) -> Expr:
            """"""
            return strx.to_sentence_case(self._expr)

        def to_sponge_case(self) -> Expr:
            """"""
            return strx.to_sponge_case(self._expr)

except ModuleNotFoundError:
    pass