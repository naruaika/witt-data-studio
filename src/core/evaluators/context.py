# context.py
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
