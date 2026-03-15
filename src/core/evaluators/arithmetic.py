# arithmetic.py
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
