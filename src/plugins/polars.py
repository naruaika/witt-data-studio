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

from polars import Expr
from polars.api import register_expr_namespace
from warnings import deprecated

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



def initialize() -> None:
    """"""
    pass