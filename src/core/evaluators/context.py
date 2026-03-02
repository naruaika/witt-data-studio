# context.py
#
# Copyright (c) 2025 Naufan Rusyda Faikar <hello@naruaika.me>
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

from functools import reduce
import ast
import operator

class Evaluator():

    OPERATORS = {ast.Gt:    operator.gt,
                 ast.Lt:    operator.lt,
                 ast.Eq:    operator.eq,
                 ast.NotEq: operator.ne,
                 ast.GtE:   operator.ge,
                 ast.LtE:   operator.le,
                 ast.Not:   operator.not_,
                 ast.And:   all,
                 ast.Or:    any}

    def __init__(self, vars: dict):
        """"""
        super().__init__()

        self.vars = vars

    def evaluate(self, expr: str):
        """"""
        tree = ast.parse(expr, mode = 'eval')
        return self._visit(tree.body)

    def _visit(self, node):
        """"""
        if isinstance(node, ast.Name):
            return self.vars.get(node.id, node.id)

        if isinstance(node, ast.Constant):
            return node.value

        if isinstance(node, ast.Compare):
            op = self.OPERATORS[type(node.ops[0])]
            left = self._visit(node.left)
            right = self._visit(node.comparators[0])
            return op(left, right)

        if isinstance(node, ast.BoolOp):
            values = [self._visit(v) for v in node.values]
            if isinstance(node.op, ast.And):
                return reduce(operator.and_, values)
            elif isinstance(node.op, ast.Or):
                return reduce(operator.or_, values)
            return values

        if isinstance(node, ast.UnaryOp):
            op = self.OPERATORS[type(node.op)]
            return op(self._visit(node.operand))

        raise TypeError(f"Syntax '{type(node).__name__}' is not allowed.")



def initialize() -> None:
    """"""
    pass
