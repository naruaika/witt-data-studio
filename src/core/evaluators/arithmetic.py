# arithmetic.py
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

import ast
import operator

class Evaluator():

    OPERATORS = {ast.Add:      operator.add,
                 ast.Sub:      operator.sub,
                 ast.Mult:     operator.mul,
                 ast.Div:      operator.truediv,
                 ast.FloorDiv: operator.floordiv,
                 ast.Mod:      operator.mod,
                 ast.Pow:      operator.pow,
                 ast.UAdd:     operator.pos,
                 ast.USub:     operator.neg}

    def evaluate(self, expr: str):
        """"""
        tree = ast.parse(expr, mode = 'eval')
        return self._visit(tree.body)

    def _visit(self, node):
        """"""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise TypeError('Only numbers are allowed')

        if isinstance(node, ast.BinOp):
            left = self._visit(node.left)
            right = self._visit(node.right)
            op = self.OPERATORS[type(node.op)]
            return op(left, right)

        if isinstance(node, ast.UnaryOp):
            op = self.OPERATORS[type(node.op)]
            return op(self._visit(node.operand))

        raise TypeError(f"Syntax '{type(node).__name__}' is not allowed.")



def initialize() -> None:
    """"""
    pass
