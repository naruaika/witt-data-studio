# test_parser_sheet_formula.py
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


from src.core.parser_sheet_formula import Transformer
from src.core.parser_sheet_formula import parser
from typing import Any
import polars

class TestParserSheetFormula:

    tables = {
        'Table 1' : polars.DataFrame({
            'foo' : [  1,   2,   3,   4  ],
            'bar' : [ 6.0, 7.0, 8.0, 9.0 ],
            'ham' : [ 'a', 'b', 'c', 'c' ],
        }),
        'Table 2' : polars.DataFrame({
            'foo' : [ 1, 2, 3, 4 ],
            'bar' : [ 1, 2, 2, 1 ],
        })
    }

    def _run_formula(self, formula: str) -> Any:
        """"""
        tree = parser.parse(formula)
        transformer = Transformer({}, self.tables)
        result = transformer.transform(tree)
        result = transformer.collect(result)
        return result

    def test_1(self) -> None:
        """"""
        formula = '= TABLE({"foo": [1, 2, 3, 4], "bar": [1, 2, 2, 1]})'
        result = self._run_formula(formula)
        assert polars.DataFrame({
            'foo' : [ 1, 2, 3, 4 ],
            'bar' : [ 1, 2, 2, 1 ],
        }).equals(result)

        from datetime import date
        formula = """= TABLE({
            "foo": [1, 2, 3],
            "bar": [6.0, 7.0, 8.0],
            "ham": [DATE(2020, 1, 2), DATE(2021, 3, 4), DATE(2022, 5, 6)],
        })"""
        result = self._run_formula(formula)
        assert polars.DataFrame({
            "foo": [ 1,                2,                3                ],
            "bar": [ 6.0,              7.0,              8.0              ],
            "ham": [ date(2020, 1, 2), date(2021, 3, 4), date(2022, 5, 6) ],
        }).equals(result)

    def test_2(self) -> None:
        """"""
        formula = '= TABLE("Table 2").BOTTOMK(2, by="bar")'
        result = self._run_formula(formula)
        assert polars.DataFrame({
            "foo": [ 1, 4 ],
            "bar": [ 1, 1 ],
        }).equals(result)

        formula = '= TABLE("Table 2").BOTTOMK(2, by=["foo", "bar"])'
        result = self._run_formula(formula)
        assert polars.DataFrame({
            "foo": [ 1, 2 ],
            "bar": [ 1, 2 ],
        }).equals(result)

        formula = "= TABLE('Table 1').CAST({'bar': TYPE.INT16})"
        result = self._run_formula(formula)
        assert polars.DataFrame({
            "foo": [  1,   2,   3,   4  ],
            "bar": [  6,   7,   8,   9  ],
            "ham": [ 'a', 'b', 'c', 'c' ],
        }).equals(result)

    def test_3(self) -> None:
        """"""
        formula = '= TABLE("Table 1").FILTER(COLUMN("foo") > 1)'
        result = self._run_formula(formula)
        assert polars.DataFrame({
            "foo": [  2,   3,   4  ],
            "bar": [  7,   8,   9  ],
            "ham": [ 'b', 'c', 'c' ],
        }).equals(result)

        formula = '= TABLE("Table 1").FILTER((1 < COLUMN("foo")) & (COLUMN("bar") > 7))'
        result = self._run_formula(formula)
        assert polars.DataFrame({
            "foo": [  3,   4  ],
            "bar": [ 8.0, 9.0 ],
            "ham": [ 'c', 'c' ],
        }).equals(result)

    def test_4(self) -> None:
        """"""
        formula = '= TABLE("Table 1").GROUPBY("ham").AGG(COLUMN("foo").SUM()).SORT("foo")'
        result = self._run_formula(formula)
        assert polars.DataFrame({
            "ham": [ 'a', 'b', 'c' ],
            "foo": [  1,   2,   7  ],
        }).equals(result)

    def test_5(self) -> None:
        """"""
        formula = "= TABLE('Table 1').SELECT(ALLCOLUMNS())"
        result = self._run_formula(formula)
        assert polars.DataFrame({
            "foo": [  1,   2,   3,   4  ],
            "bar": [ 6.0, 7.0, 8.0, 9.0 ],
            "ham": [ 'a', 'b', 'c', 'c' ],
        }).equals(result)

        formula = "= TABLE('Table 1').SELECT(COLUMN('*').COUNT())"
        result = self._run_formula(formula)
        assert polars.DataFrame({
            "foo": [ 4 ],
            "bar": [ 4 ],
            "ham": [ 4 ],
        }).equals(result)

    def test_6(self) -> None:
        """"""
        formula = "= TABLE('Table 1').SELECT(COLUMN('ham').STR.TOUPPERCASE())"
        result = self._run_formula(formula)
        assert polars.DataFrame({
            "ham": [ 'A', 'B', 'C', 'C' ],
        }).equals(result)

    def test_7(self) -> None:
        """"""
        formula = "= TABLE('Table 1').WITHCOLUMNS(COLUMN('bar').CAST(TYPE.INT16))"
        result = self._run_formula(formula)
        assert polars.DataFrame({
            "foo": [  1,   2,   3,   4  ],
            "bar": [  6,   7,   8,   9  ],
            "ham": [ 'a', 'b', 'c', 'c' ],
        }).equals(result)

    def test_8(self) -> None:
        """"""
        formula = "= TABLE('Table 1').SELECT(COLUMN('ham').STR.TOUPPERCASE() + 'X')"
        result = self._run_formula(formula)
        assert polars.DataFrame({
            "ham": [ 'AX', 'BX', 'CX', 'CX' ],
        }).equals(result)

    def test_9(self) -> None:
        """"""
        formula = """>
        expression = COLUMN("foo") > 2
        TABLE('Table 1').FILTER(expression)
        """
        result = self._run_formula(formula)
        assert polars.DataFrame({
            "foo": [  3,   4  ],
            "bar": [ 8.0, 9.0 ],
            "ham": [ 'c', 'c' ],
        }).equals(result)

        formula = """>
        literal = 2
        expression = (COLUMN("foo") >= literal) &
                     (COLUMN("bar") >= literal)
        TABLE('Table 2').FILTER(expression)
        """
        result = self._run_formula(formula)
        assert polars.DataFrame({
            "foo": [ 2, 3 ],
            "bar": [ 2, 2 ],
        }).equals(result)