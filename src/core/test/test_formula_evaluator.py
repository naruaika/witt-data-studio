# test_formula_evaluator.py
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


from src.core.formula_evaluator import Evaluator
from typing import Any
import os
import polars

class TestParserSheetFormula:

    vars = {
        'Table1': polars.DataFrame({
            'foo': [  1,   2,   3,   4  ],
            'bar': [ 6.0, 7.0, 8.0, 9.0 ],
            'ham': [ 'a', 'b', 'c', 'c' ],
        }),
        'Table2': polars.DataFrame({
            'foo': [ 1, 2, 3, 4 ],
            'bar': [ 1, 2, 2, 1 ],
        })
    }

    def evaluate(self, formula: str) -> Any:
        """"""
        return Evaluator(self.vars).evaluate(formula)

    def test_1(self) -> None:
        """"""
        formula = 'DataFrame({"foo": [1, 2, 3, 4], "bar": [1, 2, 2, 1]})'
        result = self.evaluate(formula)
        assert polars.DataFrame({
            'foo': [ 1, 2, 3, 4 ],
            'bar': [ 1, 2, 2, 1 ],
        }).equals(result)

        from datetime import date
        formula = """DataFrame({
            "foo": [1, 2, 3],
            "bar": [6.0, 7.0, 8.0],
            "ham": [Date(2020, 1, 2), Date(2021, 3, 4), Date(2022, 5, 6)],
        })"""
        result = self.evaluate(formula)
        assert polars.DataFrame({
            "foo": [ 1,                2,                3                ],
            "bar": [ 6.0,              7.0,              8.0              ],
            "ham": [ date(2020, 1, 2), date(2021, 3, 4), date(2022, 5, 6) ],
        }).equals(result)

    def test_2(self) -> None:
        """"""
        formula = 'Table1'
        result = self.evaluate(formula)
        assert polars.DataFrame({
            'foo': [  1,   2,   3,   4  ],
            'bar': [ 6.0, 7.0, 8.0, 9.0 ],
            'ham': [ 'a', 'b', 'c', 'c' ],
        }).equals(result)

        formula = 'Table2.bottom_k(2, by="bar")'
        result = self.evaluate(formula)
        assert polars.DataFrame({
            "foo": [ 1, 4 ],
            "bar": [ 1, 1 ],
        }).equals(result)

        formula = "Table2.bottom_k(2, by=['foo', 'bar'])"
        result = self.evaluate(formula)
        assert polars.DataFrame({
            "foo": [ 1, 2 ],
            "bar": [ 1, 2 ],
        }).equals(result)

        formula = 'Table1.cast({"bar": Type.Int16})'
        result = self.evaluate(formula)
        assert polars.DataFrame({
            "foo": [  1,   2,   3,   4  ],
            "bar": [  6,   7,   8,   9  ],
            "ham": [ 'a', 'b', 'c', 'c' ],
        }).equals(result)

    def test_3(self) -> None:
        """"""
        formula = 'Table1.filter(Column("foo") > 1)'
        result = self.evaluate(formula)
        assert polars.DataFrame({
            "foo": [  2,   3,   4  ],
            "bar": [  7,   8,   9  ],
            "ham": [ 'b', 'c', 'c' ],
        }).equals(result)

        formula = 'Table1.filter((1 < Column("foo")) & (Column("bar") > 7))'
        result = self.evaluate(formula)
        assert polars.DataFrame({
            "foo": [  3,   4  ],
            "bar": [ 8.0, 9.0 ],
            "ham": [ 'c', 'c' ],
        }).equals(result)

    def test_4(self) -> None:
        """"""
        formula = 'Table1.group_by("ham").agg(Column("foo").sum()).sort("foo")'
        result = self.evaluate(formula)
        assert polars.DataFrame({
            "ham": [ 'a', 'b', 'c' ],
            "foo": [  1,   2,   7  ],
        }).equals(result)

    def test_5(self) -> None:
        """"""
        formula = "Table1.select(Column('*'))"
        result = self.evaluate(formula)
        assert polars.DataFrame({
            "foo": [  1,   2,   3,   4  ],
            "bar": [ 6.0, 7.0, 8.0, 9.0 ],
            "ham": [ 'a', 'b', 'c', 'c' ],
        }).equals(result)

        formula = "Table1.select(Column('*').count())"
        result = self.evaluate(formula)
        assert polars.DataFrame({
            "foo": [ 4 ],
            "bar": [ 4 ],
            "ham": [ 4 ],
        }).equals(result)

    def test_6(self) -> None:
        """"""
        formula = "Table1.select(Column('ham').str.to_uppercase())"
        result = self.evaluate(formula)
        assert polars.DataFrame({
            "ham": [ 'A', 'B', 'C', 'C' ],
        }).equals(result)

    def test_7(self) -> None:
        """"""
        formula = "Table1.with_columns(Column('bar').cast(Type.Int16))"
        result = self.evaluate(formula)
        assert polars.DataFrame({
            "foo": [  1,   2,   3,   4  ],
            "bar": [  6,   7,   8,   9  ],
            "ham": [ 'a', 'b', 'c', 'c' ],
        }).equals(result)

    def test_8(self) -> None:
        """"""
        formula = "Table1.select(Column('ham').str.to_uppercase() + 'X')"
        result = self.evaluate(formula)
        assert polars.DataFrame({
            "ham": [ 'AX', 'BX', 'CX', 'CX' ],
        }).equals(result)

    def test_9(self) -> None:
        """"""
        formula = """
expression = Column("foo") > 2
Table1.filter(expression)
        """
        result = self.evaluate(formula)
        assert polars.DataFrame({
            "foo": [  3,   4  ],
            "bar": [ 8.0, 9.0 ],
            "ham": [ 'c', 'c' ],
        }).equals(result)

        formula = """
literal = 2
expression = (Column("foo") >= literal) & \
             (Column("bar") >= literal)
Table2.filter(expression)
        """
        result = self.evaluate(formula)
        assert polars.DataFrame({
            "foo": [ 2, 3 ],
            "bar": [ 2, 2 ],
        }).equals(result)

    def test_10(self) -> None:
        """"""
        fpath = 'file.out'

        formula = f"Table1.write_csv('{fpath}')"
        result = self.evaluate(formula)
        assert result is None

        formula = "Table1.write_csv()"
        result = self.evaluate(formula)
        assert result == 'foo,bar,ham\n' \
                         '1,6.0,a\n' \
                         '2,7.0,b\n' \
                         '3,8.0,c\n' \
                         '4,9.0,c\n'

        if os.path.exists(fpath):
            os.remove(fpath)

    def test_11(self) -> None:
        """"""
        formula = "123"
        result = self.evaluate(formula)
        assert result == 123

        formula = "[1, 2, 3]"
        result = self.evaluate(formula)
        assert result == [1, 2, 3]

        formula = "(1, 2, 3)"
        result = self.evaluate(formula)
        assert result == (1, 2, 3)

        formula = "{'a': 1, 'b': 2, 'c': 3}"
        result = self.evaluate(formula)
        assert result == {'a': 1, 'b': 2, 'c': 3}

    def test_12(self) -> None:
        """"""
        formula = "(lambda x: x + 1)(5)"
        result = self.evaluate(formula)
        assert result == 6

    def test_13(self) -> None:
        """"""
        formula = 'Table1.filter(~(Column("foo") > 1))'
        result = self.evaluate(formula)
        assert polars.DataFrame({
            "foo": [  1,  ],
            "bar": [ 6.0, ],
            "ham": [ 'a', ],
        }).equals(result)
