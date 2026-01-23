# parser_command_context.py
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

from lark import Lark
from lark import Transformer
from lark import v_args
from typing import Any
import operator

_GRAMMAR = r"""
    ?start: logical_or

    ?logical_or:  logical_and ("or" logical_and)*
    ?logical_and: term ("and" term)*
    logical_not:  "not" atom

    ?term:  logical_not | atom
    ?atom:  comparison | "(" logical_or ")"
    ?const: NAME | NUMBER

    ?comparison: const (OPERATOR const)?

    OPERATOR: ">=" | "<=" | "!=" | "==" | ">" | "<"

    %import common.CNAME -> NAME
    %import common.NUMBER
    %import common.WS
    %ignore WS
"""


@v_args(inline=True)
class Transformer(Transformer):

    OPERATORS = {'>=' : operator.ge,
                 '<=' : operator.le,
                 '!=' : operator.ne,
                 '==' : operator.eq,
                 '>'  : operator.gt,
                 '<'  : operator.lt}

    def __init__(self, vars: dict) -> None:
        """"""
        self.vars = vars

    def logical_or(self, *args) -> bool:
        """"""
        return any(args)

    def logical_and(self, *args) -> bool:
        """"""
        return all(args)

    def logical_not(self, arg) -> bool:
        """"""
        return not arg

    def comparison(self, *args) -> bool:
        """"""
        if len(args) == 1:
            return args[0]
        left, op, right = args
        op = self.OPERATORS[str(op)]
        return op(left, right)

    def NAME(self, arg) -> Any:
        """"""
        try:
            return self.vars[arg]
        except:
            return arg

    def NUMBER(self, arg) -> float:
        """"""
        return float(arg)


parser = Lark(_GRAMMAR, parser = 'lalr')
