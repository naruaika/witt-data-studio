# parser_sheet_formula.py
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

from __future__ import annotations
from lark import Lark
from lark import Token
from lark import Transformer
from lark import v_args
from polars import DataFrame
from polars import DataType
from polars import Expr as Expression
from polars.dataframe.group_by import DynamicGroupBy
from polars.dataframe.group_by import GroupBy
from polars.dataframe.group_by import RollingGroupBy
from polars import Series
from datetime import datetime
from datetime import date
from datetime import time
import operator

from .utils import parse_table_rpath

_GRAMMAR = r"""
    ?start: single_line | multi_line

    single_line: "=" formula
    multi_line:  ">" script

    ?script:    (NEWLINE* assignment)* NEWLINE* formula [NEWLINE*]
    assignment: NAME "=" formula

    ?formula:     bitwise_or
    ?bitwise_or:  bitwise_xor (BITWISE_OR bitwise_xor)*
    ?bitwise_xor: bitwise_and (BITWISE_XOR bitwise_and)*
    ?bitwise_and: comparison  (BITWISE_AND comparison)*

    ?comparison: summation (COMPARATOR summation)*
    ?summation:  product   (SUMMATOR product)*
    ?product:    exponent  (PRODUCTOR exponent)*
    ?exponent:   unary     (EXPONENTOR exponent)?

    ?unary: UNATOR unary | atom

    ?atom: primary (call | "." NAME call?)*
    call:  "(" [arguments] ")"

    ?primary: "(" formula ")"
            | table
            | column
            | list
            | dict
            | NUMBER
            | STRING
            | NAME

    tuple: "(" [formula ("," formula)* [","]] ")"
    list:  "[" [formula ("," formula)* [","]] "]"
    dict:  "{" [pair ("," pair)* [","]] "}"
    pair:  (STRING | NUMBER | tuple) ":" formula

    table:  "t" STRING
    column: "c" STRING

    arguments:     argument ("," argument)* [","]
    argument:      (formula | pair_argument)
    pair_argument: NAME "=" formula

    COMPARATOR: ">" | "<" | "==" | "!=" | ">=" | "<="
    SUMMATOR:   "+" | "-"
    PRODUCTOR:  "*" | "/" | "//" | "%"
    EXPONENTOR: "**"
    UNATOR:     "~" | "not"

    BITWISE_OR:  "|"
    BITWISE_XOR: "^"
    BITWISE_AND: "&"

    NAME: /[a-zA-Z_$][a-zA-Z0-9_$]*/

    %import common.NEWLINE
    %import common.WS_INLINE

    %ignore WS_INLINE
    %ignore NEWLINE

    %import common.SIGNED_NUMBER  -> NUMBER
    %import common.ESCAPED_STRING

    STRING: ESCAPED_STRING | SINGLE_QUOTED_STRING
    SINGLE_QUOTED_STRING: /'(\\.|[^'\\])*'/
"""


# Here we also add a proxy to each of polars objects to
# remove methods related to I/O functionality, in-place
# modification, and built-in methods. Also to add alias
# for each method so that .snake_case become .UPPERCASE
# in trying to bring familiarity of MICROSOFT POWER BI,
# POWER QUERY, and EXCEL at the expense of readibility.
# This decision is subject to change in the near future

class _SafeDataTypeMeta(type):

    def __getattr__(cls, name: str) -> DataType:
        """"""
        return _SafeDataType._getattr(name)


class _SafeDataType(metaclass = _SafeDataTypeMeta):

    def __getattr__(self, name: str) -> DataType:
        """"""
        return self._getattr(name)

    @staticmethod
    def _getattr(name: str) -> DataType:
        """"""
        _name = name.upper().replace('_', '')

        from polars import Array
        from polars import Boolean
        from polars import Categorical
        from polars import Date
        from polars import Datetime
        from polars import Decimal
        from polars import Duration
        from polars import Enum
        from polars import Field
        from polars import Float32
        from polars import Float64
        from polars import Int8
        from polars import Int16
        from polars import Int32
        from polars import Int64
        from polars import List
        from polars import String
        from polars import Struct
        from polars import Time
        from polars import UInt8
        from polars import UInt16
        from polars import UInt32
        from polars import UInt64

        attributes = {'ARRAY'       : Array,
                      'BOOLEAN'     : Boolean,
                      'CATEGORICAL' : Categorical,
                      'DATE'        : Date,
                      'DATETIME'    : Datetime,
                      'DECIMAL'     : Decimal,
                      'DURATION'    : Duration,
                      'ENUM'        : Enum,
                      'FIELD'       : Field,
                      'FLOAT32'     : Float32,
                      'FLOAT64'     : Float64,
                      'INT8'        : Int8,
                      'INT16'       : Int16,
                      'INT32'       : Int32,
                      'INT64'       : Int64,
                      'LIST'        : List,
                      'STRING'      : String,
                      'STRUCT'      : Struct,
                      'TIME'        : Time,
                      'UINT8'       : UInt8,
                      'UINT16'      : UInt16,
                      'UINT32'      : UInt32,
                      'UINT64'      : UInt64}

        if _name in attributes:
            return attributes[_name]

        raise AttributeError(f"'DataType' object has no attribute '{name}'.")


class _SafeExpressionMeta(type):

    def __getattr__(cls, name: str) -> Expression:
        """"""
        return _SafeExpression._getattr(name)


class _SafeExpression(metaclass = _SafeExpressionMeta):

    def __init__(self, expression: Expression) -> None:
        """"""
        self._expression = expression

    def __getattr__(self, name: str) -> Expression:
        """"""
        return self._getattr(name, self._expression)

    @staticmethod
    def _unwrap_args(*args, **kwargs) -> tuple[list, dict]:
        """"""
        new_args = list(args)
        for idx, arg in enumerate(new_args):
            if isinstance(arg, _SafeExpression):
                new_args[idx] = arg._expression

        new_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, _SafeExpression):
                new_kwargs[key] = value._expression
            else:
                new_kwargs[key] = value

        return new_args, new_kwargs

    @staticmethod
    def ALLCOLUMNS(*args, **kwargs) -> '_SafeExpression':
        """"""
        return _SafeExpression.ALL(*args, **kwargs)

    @staticmethod
    def COLUMN(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import col
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(col(*args, **kwargs))

    @staticmethod
    def ALL(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import all
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(all(*args, **kwargs))

    @staticmethod
    def ALLHORIZONTAL(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import all_horizontal
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(all_horizontal(*args, **kwargs))

    @staticmethod
    def ANY(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import any
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(any(*args, **kwargs))

    @staticmethod
    def ANYHORIZONTAL(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import any_horizontal
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(any_horizontal(*args, **kwargs))

    @staticmethod
    def APPROXNUNIQUE(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import approx_n_unique
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(approx_n_unique(*args, **kwargs))

    @staticmethod
    def ARANGE(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import arange
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(arange(*args, **kwargs))

    @staticmethod
    def ARCTAN2(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import arctan2
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(arctan2(*args, **kwargs))

    @staticmethod
    def ARCTAN2D(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import arctan2d
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(arctan2d(*args, **kwargs))

    @staticmethod
    def ARGSORTBY(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import arg_sort_by
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(arg_sort_by(*args, **kwargs))

    @staticmethod
    def ARGWHERE(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import arg_where
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(arg_where(*args, **kwargs))

    @staticmethod
    def BUSINESSDAYCOUNT(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import business_day_count
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(business_day_count(*args, **kwargs))

    @staticmethod
    def COALESCE(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import coalesce
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(coalesce(*args, **kwargs))

    @staticmethod
    def CONCATARR(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import concat_arr
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(concat_arr(*args, **kwargs))

    @staticmethod
    def CONCATLIST(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import concat_list
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(concat_list(*args, **kwargs))

    @staticmethod
    def CONCATSTR(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import concat_str
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(concat_str(*args, **kwargs))

    @staticmethod
    def CORR(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import corr
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(corr(*args, **kwargs))

    @staticmethod
    def COV(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import cov
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(cov(*args, **kwargs))

    @staticmethod
    def CUMCOUNT(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import cum_count
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(cum_count(*args, **kwargs))

    @staticmethod
    def CUMFOLD(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import cum_fold
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(cum_fold(*args, **kwargs))

    @staticmethod
    def CUMREDUCE(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import cum_reduce
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(cum_reduce(*args, **kwargs))

    @staticmethod
    def CUMSUM(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import cum_sum
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(cum_sum(*args, **kwargs))

    @staticmethod
    def CUMSUMHORIZONTAL(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import cum_sum_horizontal
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(cum_sum_horizontal(*args, **kwargs))

    @staticmethod
    def DATE(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import date
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(date(*args, **kwargs))

    @staticmethod
    def DATERANGE(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import date_range
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(date_range(*args, **kwargs))

    @staticmethod
    def DATERANGES(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import date_ranges
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(date_ranges(*args, **kwargs))

    @staticmethod
    def DATETIME(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import datetime
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(datetime(*args, **kwargs))

    @staticmethod
    def DATETIMERANGE(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import datetime_range
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(datetime_range(*args, **kwargs))

    @staticmethod
    def DATETIMERANGES(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import datetime_ranges
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(datetime_ranges(*args, **kwargs))

    @staticmethod
    def DURATION(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import duration
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(duration(*args, **kwargs))

    @staticmethod
    def ELEMENT(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import element
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(element(*args, **kwargs))

    @staticmethod
    def EXCLUDE(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import exclude
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(exclude(*args, **kwargs))

    @staticmethod
    def FIELD(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import field
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(field(*args, **kwargs))

    @staticmethod
    def FIRST(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import first
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(first(*args, **kwargs))

    @staticmethod
    def FOLD(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import fold
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(fold(*args, **kwargs))

    @staticmethod
    def FORMAT(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import format
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(format(*args, **kwargs))

    @staticmethod
    def FROMEPOCH(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import from_epoch
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(from_epoch(*args, **kwargs))

    @staticmethod
    def GROUPS(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import groups
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(groups(*args, **kwargs))

    @staticmethod
    def HEAD(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import head
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(head(*args, **kwargs))

    @staticmethod
    def IMPLODE(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import implode
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(implode(*args, **kwargs))

    @staticmethod
    def INTRANGE(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import int_range
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(int_range(*args, **kwargs))

    @staticmethod
    def INTRANGES(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import int_ranges
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(int_ranges(*args, **kwargs))

    @staticmethod
    def LAST(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import last
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(last(*args, **kwargs))

    @staticmethod
    def LEN(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import len
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(len(*args, **kwargs))

    @staticmethod
    def LINEARSPACE(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import linear_space
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(linear_space(*args, **kwargs))

    @staticmethod
    def LINEARSPACES(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import linear_spaces
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(linear_spaces(*args, **kwargs))

    @staticmethod
    def LIT(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import lit
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(lit(*args, **kwargs))

    @staticmethod
    def MAPBATCHES(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import map_batches
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(map_batches(*args, **kwargs))

    @staticmethod
    def MAPGROUPS(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import map_groups
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(map_groups(*args, **kwargs))

    @staticmethod
    def MAX(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import max
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(max(*args, **kwargs))

    @staticmethod
    def MAXHORIZONTAL(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import max_horizontal
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(max_horizontal(*args, **kwargs))

    @staticmethod
    def MEAN(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import mean
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(mean(*args, **kwargs))

    @staticmethod
    def MEANHORIZONTAL(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import mean_horizontal
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(mean_horizontal(*args, **kwargs))

    @staticmethod
    def MEDIAN(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import median
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(median(*args, **kwargs))

    @staticmethod
    def MIN(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import min
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(min(*args, **kwargs))

    @staticmethod
    def MINHORIZONTAL(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import min_horizontal
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(min_horizontal(*args, **kwargs))

    @staticmethod
    def NUNIQUE(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import n_unique
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(n_unique(*args, **kwargs))

    @staticmethod
    def NTH(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import nth
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(nth(*args, **kwargs))

    @staticmethod
    def ONES(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import ones
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(ones(*args, **kwargs))

    @staticmethod
    def QUANTILE(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import quantile
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(quantile(*args, **kwargs))

    @staticmethod
    def REDUCE(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import reduce
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(reduce(*args, **kwargs))

    @staticmethod
    def REPEAT(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import repeat
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(repeat(*args, **kwargs))

    @staticmethod
    def ROLLINGCORR(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import rolling_corr
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(rolling_corr(*args, **kwargs))

    @staticmethod
    def ROLLINGCOV(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import rolling_cov
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(rolling_cov(*args, **kwargs))

    @staticmethod
    def ROWINDEX(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import row_index
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(row_index(*args, **kwargs))

    @staticmethod
    def SELECT(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import select
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(select(*args, **kwargs))

    @staticmethod
    def SQL(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import sql
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(sql(*args, **kwargs))

    @staticmethod
    def SQLEXPR(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import sql_expr
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(sql_expr(*args, **kwargs))

    @staticmethod
    def STD(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import std
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(std(*args, **kwargs))

    @staticmethod
    def STRUCT(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import struct
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(struct(*args, **kwargs))

    @staticmethod
    def SUMHORIZONTAL(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import sum_horizontal
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(sum_horizontal(*args, **kwargs))

    @staticmethod
    def TAIL(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import tail
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(tail(*args, **kwargs))

    @staticmethod
    def TIME(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import time
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(time(*args, **kwargs))

    @staticmethod
    def TIMERANGE(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import time_range
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(time_range(*args, **kwargs))

    @staticmethod
    def TIMERANGES(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import time_ranges
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(time_ranges(*args, **kwargs))

    @staticmethod
    def VAR(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import var
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(var(*args, **kwargs))

    @staticmethod
    def WHEN(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import when
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(when(*args, **kwargs))

    @staticmethod
    def ZEROS(*args, **kwargs) -> '_SafeExpression':
        """"""
        from polars import zeros
        args, kwargs = _SafeExpression._unwrap_args(*args, **kwargs)
        return _SafeExpression(zeros(*args, **kwargs))

    @staticmethod
    def _getattr(name: str, expression: Expression) -> '_SafeExpression':
        """"""
        _name = name.upper().replace('_', '')

        safe_methods = {# General
                        'ABS'                    : 'abs',
                        'ADD'                    : 'add',
                        'AGGGROUPS'              : 'agg_groups',
                        'ALIAS'                  : 'alias',
                        'ALL'                    : 'all',
                        'AND'                    : 'and_',
                        'ANY'                    : 'any',
                        'APPEND'                 : 'append',
                        'APPROXNUNIQUE'          : 'approx_n_unique',
                        'ARCCOS'                 : 'arccos',
                        'ARCCOSH'                : 'arccosh',
                        'ARCSIN'                 : 'arcsin',
                        'ARCSINH'                : 'arcsinh',
                        'ARCTAN'                 : 'arctan',
                        'ARCTANH'                : 'arctanh',
                        'ARGMAX'                 : 'arg_max',
                        'ARGMIN'                 : 'arg_min',
                        'ARGSORT'                : 'arg_sort',
                        'ARGTRUE'                : 'arg_true',
                        'ARGUNIQUE'              : 'arg_unique',
                        'BACKWARDFILL'           : 'backward_fill',
                        'BITWISEAND'             : 'bitwise_and',
                        'BITWISECOUNTONES'       : 'bitwise_count_ones',
                        'BITWISECOUNTZEROS'      : 'bitwise_count_zeros',
                        'BITWISELEADINGONES'     : 'bitwise_leading_ones',
                        'BITWISELEADINGZEROS'    : 'bitwise_leading_zeros',
                        'BITWISEOR'              : 'bitwise_or',
                        'BITWISETRAILINGONES'    : 'bitwise_trailing_ones',
                        'BITWISETRAILINGZEROS'   : 'bitwise_trailing_zeros',
                        'BITWISEXOR'             : 'bitwise_xor',
                        'BOTTOMK'                : 'bottom_k',
                        'BOTTOMKBY'              : 'bottom_k_by',
                        'CAST'                   : 'cast',
                        'CBRT'                   : 'cbrt',
                        'CEIL'                   : 'ceil',
                        'CLIP'                   : 'clip',
                        'COS'                    : 'cos',
                        'COSH'                   : 'cosh',
                        'COT'                    : 'cot',
                        'COUNT'                  : 'count',
                        'CUMCOUNT'               : 'cum_count',
                        'CUMMAX'                 : 'cum_max',
                        'CUMMIN'                 : 'cum_min',
                        'CUMPROD'                : 'cum_prod',
                        'CUMSUM'                 : 'cum_sum',
                        'CUMULATIVEEVAL'         : 'cumulative_eval',
                        'CUT'                    : 'cut',
                        'DEGREES'                : 'degrees',
                        'DIFF'                   : 'diff',
                        'DOT'                    : 'dot',
                        'DROPNANS'               : 'drop_nans',
                        'DROPNULLS'              : 'drop_nulls',
                        'ENTROPY'                : 'entropy',
                        'EQ'                     : 'eq',
                        'EQMISSING'              : 'eq_missing',
                        'EWMMEAN'                : 'ewm_mean',
                        'EWMMEANBY'              : 'ewm_mean_by',
                        'EWMSTD'                 : 'ewm_std',
                        'EWMVAR'                 : 'ewm_var',
                        'EXCLUDE'                : 'exclude',
                        'EXP'                    : 'exp',
                        'EXPLODE'                : 'explode',
                        'EXTENDCONSTANT'         : 'extend_constant',
                        'FILLNAN'                : 'fill_nan',
                        'FILLNULL'               : 'fill_null',
                        'FILTER'                 : 'filter',
                        'FIRST'                  : 'first',
                        'FLATTEN'                : 'flatten',
                        'FLOOR'                  : 'floor',
                        'FLOORDIV'               : 'floordiv',
                        'FORWARDFILL'            : 'forward_fill',
                        'GATHER'                 : 'gather',
                        'GATHEREVERY'            : 'gather_every',
                        'GE'                     : 'ge',
                        'GET'                    : 'get',
                        'GT'                     : 'gt',
                        'HASNULLS'               : 'has_nulls',
                        'HASH'                   : 'hash',
                        'HEAD'                   : 'head',
                        'HIST'                   : 'hist',
                        'IMPLODE'                : 'implode',
                        'INDEXOF'                : 'index_of',
                        'INTERPOLATE'            : 'interpolate',
                        'INTERPOLATEBY'          : 'interpolate_by',
                        'ISBETWEEN'              : 'is_between',
                        'ISCLOSE'                : 'is_close',
                        'ISDUPLICATED'           : 'is_duplicated',
                        'ISFINITE'               : 'is_finite',
                        'ISFIRSTDISTINCT'        : 'is_first_distinct',
                        'ISIN'                   : 'is_in',
                        'ISINFINITE'             : 'is_infinite',
                        'ISLASTDISTINCT'         : 'is_last_distinct',
                        'ISNAN'                  : 'is_nan',
                        'ISNOTNAN'               : 'is_not_nan',
                        'ISNOTNULL'              : 'is_not_null',
                        'ISNULL'                 : 'is_null',
                        'ISUNIQUE'               : 'is_unique',
                        'ITEM'                   : 'item',
                        'KURTOSIS'               : 'kurtosis',
                        'LAST'                   : 'last',
                        'LE'                     : 'le',
                        'LEN'                    : 'len',
                        'LIMIT'                  : 'limit',
                        'LOG'                    : 'log',
                        'LOG10'                  : 'log10',
                        'LOG1P'                  : 'log1p',
                        'LOWERBOUND'             : 'lower_bound',
                        'LT'                     : 'lt',
                        'MAPBATCHES'             : 'map_batches',
                        'MAPELEMENTS'            : 'map_elements',
                        'MAX'                    : 'max',
                        'MEAN'                   : 'mean',
                        'MEDIAN'                 : 'median',
                        'MIN'                    : 'min',
                        'MOD'                    : 'mod',
                        'MODE'                   : 'mode',
                        'MUL'                    : 'mul',
                        'NUNIQUE'                : 'n_unique',
                        'NANMAX'                 : 'nan_max',
                        'NANMIN'                 : 'nan_min',
                        'NE'                     : 'ne',
                        'NEMISSING'              : 'ne_missing',
                        'NEG'                    : 'neg',
                        'NOT'                    : 'not_',
                        'NULLCOUNT'              : 'null_count',
                        'OR'                     : 'or_',
                        'OVER'                   : 'over',
                        'PCTCHANGE'              : 'pct_change',
                        'PEAKMAX'                : 'peak_max',
                        'PEAKMIN'                : 'peak_min',
                        'PIPE'                   : 'pipe',
                        'POW'                    : 'pow',
                        'PRODUCT'                : 'product',
                        'QCUT'                   : 'qcut',
                        'QUANTILE'               : 'quantile',
                        'RADIANS'                : 'radians',
                        'RANK'                   : 'rank',
                        'RECHUNK'                : 'rechunk',
                        'REINTERPRET'            : 'reinterpret',
                        'REPEATBY'               : 'repeat_by',
                        'REPLACE'                : 'replace',
                        'REPLACESTRICT'          : 'replace_strict',
                        'RESHAPE'                : 'reshape',
                        'REVERSE'                : 'reverse',
                        'RLE'                    : 'rle',
                        'RLEID'                  : 'rle_id',
                        'ROLLING'                : 'rolling',
                        'ROLLINGKURTOSIS'        : 'rolling_kurtosis',
                        'ROLLINGMAP'             : 'rolling_map',
                        'ROLLINGMAX'             : 'rolling_max',
                        'ROLLINGMAXBY'           : 'rolling_max_by',
                        'ROLLINGMEAN'            : 'rolling_mean',
                        'ROLLINGMEANBY'          : 'rolling_mean_by',
                        'ROLLINGMEDIAN'          : 'rolling_median',
                        'ROLLINGMEDIANBY'        : 'rolling_median_by',
                        'ROLLINGMIN'             : 'rolling_min',
                        'ROLLINGMINBY'           : 'rolling_min_by',
                        'ROLLINGQUANTILE'        : 'rolling_quantile',
                        'ROLLINGQUANTILEBY'      : 'rolling_quantile_by',
                        'ROLLINGRANK'            : 'rolling_rank',
                        'ROLLINGRANKBY'          : 'rolling_rank_by',
                        'ROLLINGSKEW'            : 'rolling_skew',
                        'ROLLINGSTD'             : 'rolling_std',
                        'ROLLINGSTDBY'           : 'rolling_std_by',
                        'ROLLINGSUM'             : 'rolling_sum',
                        'ROLLINGSUMBY'           : 'rolling_sum_by',
                        'ROLLINGVAR'             : 'rolling_var',
                        'ROLLINGVARBY'           : 'rolling_var_by',
                        'ROUND'                  : 'round',
                        'ROUNDSIGFIGS'           : 'round_sig_figs',
                        'SAMPLE'                 : 'sample',
                        'SEARCHSORTED'           : 'search_sorted',
                        'SETSORTED'              : 'set_sorted',
                        'SHIFT'                  : 'shift',
                        'SHRINKDTYPE'            : 'shrink_dtype',
                        'SHUFFLE'                : 'shuffle',
                        'SIGN'                   : 'sign',
                        'SIN'                    : 'sin',
                        'SINH'                   : 'sinh',
                        'SKEW'                   : 'skew',
                        'SLICE'                  : 'slice',
                        'SORT'                   : 'sort',
                        'SORTBY'                 : 'sort_by',
                        'SQRT'                   : 'sqrt',
                        'STD'                    : 'std',
                        'SUB'                    : 'sub',
                        'SUM'                    : 'sum',
                        'TAIL'                   : 'tail',
                        'TAN'                    : 'tan',
                        'TANH'                   : 'tanh',
                        'TOPHYSICAL'             : 'to_physical',
                        'TOPK'                   : 'top_k',
                        'TOPKBY'                 : 'top_k_by',
                        'TRUEDIV'                : 'truediv',
                        'UNIQUE'                 : 'unique',
                        'UNIQUECOUNTS'           : 'unique_counts',
                        'UPPERBOUND'             : 'upper_bound',
                        'VALUECOUNTS'            : 'value_counts',
                        'VAR'                    : 'var',
                        'XOR'                    : 'xor',

                        # arr.
                        'AGG'                    : 'agg',
                        'ALL'                    : 'all',
                        'ANY'                    : 'any',
                        'ARGMAX'                 : 'arg_max',
                        'ARGMIN'                 : 'arg_min',
                        'CONTAINS'               : 'contains',
                        'COUNTMATCHES'           : 'count_matches',
                        'EXPLODE'                : 'explode',
                        'EVAL'                   : 'eval',
                        'FIRST'                  : 'first',
                        'GET'                    : 'get',
                        'JOIN'                   : 'join',
                        'LAST'                   : 'last',
                        'LEN'                    : 'len',
                        'MAX'                    : 'max',
                        'MEAN'                   : 'mean',
                        'MEDIAN'                 : 'median',
                        'MIN'                    : 'min',
                        'NUNIQUE'                : 'n_unique',
                        'REVERSE'                : 'reverse',
                        'SHIFT'                  : 'shift',
                        'SORT'                   : 'sort',
                        'STD'                    : 'std',
                        'SUM'                    : 'sum',
                        'TOLIST'                 : 'to_list',
                        'TOSTRUCT'               : 'to_struct',
                        'UNIQUE'                 : 'unique',
                        'VAR'                    : 'var',

                        # bin.
                        'CONTAINS'               : 'contains',
                        'DECODE'                 : 'decode',
                        'ENCODE'                 : 'encode',
                        'ENDSWITH'               : 'ends_with',
                        'REINTERPRET'            : 'reinterpret',
                        'SIZE'                   : 'size',
                        'STARTSWITH'             : 'starts_with',

                        # cat.
                        'ENDSWITH'               : 'ends_with',
                        'GETCATEGORIES'          : 'get_categories',
                        'LENBYTES'               : 'len_bytes',
                        'LENCHARS'               : 'len_chars',
                        'STARTSWITH'             : 'starts_with',

                        # dt.
                        'ADDBUSINESSDAYS'        : 'add_business_days',
                        'BASEUTCOFFSET'          : 'base_utc_offset',
                        'CASTTIMEUNIT'           : 'cast_time_unit',
                        'CENTURY'                : 'century',
                        'COMBINE'                : 'combine',
                        'CONVERTTIMEZONE'        : 'convert_time_zone',
                        'DATE'                   : 'date',
                        'DATETIME'               : 'datetime',
                        'DAY'                    : 'day',
                        'DAYSINMONTH'            : 'days_in_month',
                        'DSTOFFSET'              : 'dst_offset',
                        'EPOCH'                  : 'epoch',
                        'HOUR'                   : 'hour',
                        'ISBUSINESSDAY'          : 'is_business_day',
                        'ISLEAPYEAR'             : 'is_leap_year',
                        'ISOYEAR'                : 'iso_year',
                        'MICROSECOND'            : 'microsecond',
                        'MILLENNIUM'             : 'millennium',
                        'MILLISECOND'            : 'millisecond',
                        'MINUTE'                 : 'minute',
                        'MONTH'                  : 'month',
                        'MONTHEND'               : 'month_end',
                        'MONTHSTART'             : 'month_start',
                        'NANOSECOND'             : 'nanosecond',
                        'OFFSETBY'               : 'offset_by',
                        'ORDINALDAY'             : 'ordinal_day',
                        'QUARTER'                : 'quarter',
                        'REPLACE'                : 'replace',
                        'REPLACETIMEZONE'        : 'replace_time_zone',
                        'ROUND'                  : 'round',
                        'SECOND'                 : 'second',
                        'STRFTIME'               : 'strftime',
                        'TIME'                   : 'time',
                        'TIMESTAMP'              : 'timestamp',
                        'TOSTRING'               : 'to_string',
                        'TOTALDAYS'              : 'total_days',
                        'TOTALHOURS'             : 'total_hours',
                        'TOTALMICROSECONDS'      : 'total_microseconds',
                        'TOTALMILLISECONDS'      : 'total_milliseconds',
                        'TOTALMINUTES'           : 'total_minutes',
                        'TOTALNANOSECONDS'       : 'total_nanoseconds',
                        'TOTALSECONDS'           : 'total_seconds',
                        'TRUNCATE'               : 'truncate',
                        'WEEK'                   : 'week',
                        'WEEKDAY'                : 'weekday',
                        'WITHTIMEUNIT'           : 'with_time_unit',
                        'YEAR'                   : 'year',

                        # list.
                        'AGG'                    : 'agg',
                        'ALL'                    : 'all',
                        'ANY'                    : 'any',
                        'ARGMAX'                 : 'arg_max',
                        'ARGMIN'                 : 'arg_min',
                        'CONCAT'                 : 'concat',
                        'CONTAINS'               : 'contains',
                        'COUNTMATCHES'           : 'count_matches',
                        'DIFF'                   : 'diff',
                        'DROPNULLS'              : 'drop_nulls',
                        'EVAL'                   : 'eval',
                        'EXPLODE'                : 'explode',
                        'FILTER'                 : 'filter',
                        'FIRST'                  : 'first',
                        'GATHER'                 : 'gather',
                        'GATHEREVERY'            : 'gather_every',
                        'GET'                    : 'get',
                        'HEAD'                   : 'head',
                        'ITEM'                   : 'item',
                        'JOIN'                   : 'join',
                        'LAST'                   : 'last',
                        'LEN'                    : 'len',
                        'MAX'                    : 'max',
                        'MEAN'                   : 'mean',
                        'MEDIAN'                 : 'median',
                        'MIN'                    : 'min',
                        'NUNIQUE'                : 'n_unique',
                        'REVERSE'                : 'reverse',
                        'SAMPLE'                 : 'sample',
                        'SETDIFFERENCE'          : 'set_difference',
                        'SETINTERSECTION'        : 'set_intersection',
                        'SETSYMMETRICDIFFERENCE' : 'set_symmetric_difference',
                        'SETUNION'               : 'set_union',
                        'SHIFT'                  : 'shift',
                        'SLICE'                  : 'slice',
                        'SORT'                   : 'sort',
                        'STD'                    : 'std',
                        'SUM'                    : 'sum',
                        'TAIL'                   : 'tail',
                        'TOARRAY'                : 'to_array',
                        'TOSTRUCT'               : 'to_struct',
                        'UNIQUE'                 : 'unique',
                        'VAR'                    : 'var',

                        # meta.
                        'EQ'                     : 'eq',
                        'HASMULTIPLEOUTPUTS'     : 'has_multiple_outputs',
                        'ISCOLUMN'               : 'is_column',
                        'ISCOLUMNSELECTION'      : 'is_column_selection',
                        'ISLITERAL'              : 'is_literal',
                        'ISREGEXPROJECTION'      : 'is_regex_projection',
                        'NE'                     : 'ne',
                        'OUTPUTNAME'             : 'output_name',
                        'POP'                    : 'pop',
                        'ROOTNAMES'              : 'root_names',
                        'SERIALIZE'              : 'serialize',
                        'SHOWGRAPH'              : 'show_graph',
                        'TREEFORMAT'             : 'tree_format',
                        'UNDOALIASES'            : 'undo_aliases',

                        # name.
                        'KEEP'                   : 'keep',
                        'MAP'                    : 'map',
                        'MAPFIELDS'              : 'map_fields',
                        'PREFIX'                 : 'prefix',
                        'PREFIXFIELDS'           : 'prefix_fields',
                        'REPLACE'                : 'replace',
                        'SUFFIX'                 : 'suffix',
                        'SUFFIXFIELDS'           : 'suffix_fields',
                        'TOLOWERCASE'            : 'to_lowercase',
                        'TOUPPERCASE'            : 'to_uppercase',

                        # str.
                        'CONCAT'                 : 'concat',
                        'CONTAINS'               : 'contains',
                        'CONTAINSANY'            : 'contains_any',
                        'COUNTMATCHES'           : 'count_matches',
                        'DECODE'                 : 'decode',
                        'ENCODE'                 : 'encode',
                        'ENDSWITH'               : 'ends_with',
                        'ESCAPEREGEX'            : 'escape_regex',
                        'EXPLODE'                : 'explode',
                        'EXTRACT'                : 'extract',
                        'EXTRACTALL'             : 'extract_all',
                        'EXTRACTGROUPS'          : 'extract_groups',
                        'EXTRACTMANY'            : 'extract_many',
                        'FIND'                   : 'find',
                        'FINDMANY'               : 'find_many',
                        'HEAD'                   : 'head',
                        'JOIN'                   : 'join',
                        'JSONDECODE'             : 'json_decode',
                        'JSONPATHMATCH'          : 'json_path_match',
                        'LENBYTES'               : 'len_bytes',
                        'LENCHARS'               : 'len_chars',
                        'NORMALIZE'              : 'normalize',
                        'PADEND'                 : 'pad_end',
                        'PADSTART'               : 'pad_start',
                        'REPLACE'                : 'replace',
                        'REPLACEALL'             : 'replace_all',
                        'REPLACEMANY'            : 'replace_many',
                        'REVERSE'                : 'reverse',
                        'SLICE'                  : 'slice',
                        'SPLIT'                  : 'split',
                        'SPLITEXACT'             : 'split_exact',
                        'SPLITN'                 : 'splitn',
                        'STARTSWITH'             : 'starts_with',
                        'STRIPCHARS'             : 'strip_chars',
                        'STRIPCHARSSTART'        : 'strip_chars_start',
                        'STRIPCHARSEND'          : 'strip_chars_end',
                        'STRIPPREFIX'            : 'strip_prefix',
                        'STRIPSUFFIX'            : 'strip_suffix',
                        'STRPTIME'               : 'strptime',
                        'TAIL'                   : 'tail',
                        'TODATE'                 : 'to_date',
                        'TODATETIME'             : 'to_datetime',
                        'TODECIMAL'              : 'to_decimal',
                        'TOINTEGER'              : 'to_integer',
                        'TOLOWERCASE'            : 'to_lowercase',
                        'TOTIME'                 : 'to_time',
                        'TOTITLECASE'            : 'to_titlecase',
                        'TOUPPERCASE'            : 'to_uppercase',
                        'ZFILL'                  : 'zfill',

                        # struct.
                        'FIELD'                  : 'field',
                        'UNNEST'                 : 'unnest',
                        'JSONENCODE'             : 'json_encode',
                        'RENAMEFIELDS'           : 'rename_fields',
                        'WITHFIELDS'             : 'with_fields'}

        safe_namespaces = {'ARR'    : 'arr',
                           'BIN'    : 'bin',
                           'CAT'    : 'cat',
                           'DT'     : 'dt',
                           'LIST'   : 'list',
                           'META'   : 'meta',
                           'NAME'   : 'name',
                           'STR'    : 'str',
                           'STRUCT' : 'struct'}

        def safe_wrapper(*args, **kwargs):
            """"""
            args = list(args)
            for idx, arg in enumerate(args):
                if isinstance(arg, _SafeExpression):
                    args[idx] = arg._expression
            for key, value in kwargs:
                if isinstance(value, _SafeExpression):
                    kwargs[key] = value._expression
            name = safe_methods[_name]
            method = getattr(expression, name)
            result = method(*args, **kwargs)
            if isinstance(result, Expression):
                return _SafeExpression(result)
            return result

        if _name in safe_methods:
            return safe_wrapper

        if _name in safe_namespaces:
            name = safe_namespaces[_name]
            result = getattr(expression, name)
            return _SafeExpression(result)

        raise AttributeError(f"'Expression' object has no attribute '{name}'.")


class _SafeGroupBy:

    def __init__(self, groupby: GroupBy) -> None:
        """"""
        self._groupby = groupby

    def __getattr__(self, name: str) -> '_SafeDataFrame':
        """"""
        _name = name.upper().replace('_', '')

        safe_methods = {'AGG'       : 'agg',
                        'ALL'       : 'all',
                        'COUNT'     : 'count',
                        'FIRST'     : 'first',
                        'HEAD'      : 'head',
                        'LAST'      : 'last',
                        'LEN'       : 'len',
                        'MAPGROUPS' : 'map_groups',
                        'MAX'       : 'max',
                        'MEAN'      : 'mean',
                        'MEDIAN'    : 'median',
                        'MIN'       : 'min',
                        'NUNIQUE'   : 'n_unique',
                        'QUANTILE'  : 'quantile',
                        'SUM'       : 'sum',
                        'TAIL'      : 'tail'}

        def safe_wrapper(*args, **kwargs):
            """"""
            args = list(args)
            for idx, arg in enumerate(args):
                if isinstance(arg, _SafeExpression):
                    args[idx] = arg._expression
            for key, value in kwargs:
                if isinstance(value, _SafeExpression):
                    kwargs[key] = value._expression
            name = safe_methods[_name]
            method = getattr(self._groupby, name)
            result = method(*args, **kwargs)
            if isinstance(result, DataFrame):
                return _SafeDataFrame(result)
            return result

        if _name in safe_methods:
            return safe_wrapper

        raise AttributeError(f"'GroupBy' object has no attribute '{name}'.")


class _SafeDynamicGroupBy:

    def __init__(self, groupby: DynamicGroupBy) -> None:
        """"""
        self._groupby = groupby

    def __getattr__(self, name: str) -> '_SafeDataFrame':
        """"""
        _name = name.upper().replace('_', '')

        safe_methods = {'AGG'       : 'agg',
                        'MAPGROUPS' : 'map_groups'}

        def safe_wrapper(*args, **kwargs):
            """"""
            args = list(args)
            for idx, arg in enumerate(args):
                if isinstance(arg, _SafeExpression):
                    args[idx] = arg._expression
            for key, value in kwargs:
                if isinstance(value, _SafeExpression):
                    kwargs[key] = value._expression
            name = safe_methods[_name]
            method = getattr(self._groupby, name)
            result = method(*args, **kwargs)
            if isinstance(result, DataFrame):
                return _SafeDataFrame(result)
            return result

        if _name in safe_methods:
            return safe_wrapper

        raise AttributeError(f"'DynamicGroupBy' object has no attribute '{name}'.")


class _SafeRollingGroupBy:

    def __init__(self, groupby: RollingGroupBy) -> None:
        """"""
        self._groupby = groupby

    def __getattr__(self, name: str) -> '_SafeDataFrame':
        """"""
        _name = name.upper().replace('_', '')

        safe_methods = {'AGG'       : 'agg',
                        'MAPGROUPS' : 'map_groups'}

        def safe_wrapper(*args, **kwargs):
            """"""
            args = list(args)
            for idx, arg in enumerate(args):
                if isinstance(arg, _SafeExpression):
                    args[idx] = arg._expression
            for key, value in kwargs:
                if isinstance(value, _SafeExpression):
                    kwargs[key] = value._expression
            name = safe_methods[_name]
            method = getattr(self._groupby, name)
            result = method(*args, **kwargs)
            if isinstance(result, DataFrame):
                return _SafeDataFrame(result)
            return result

        if _name in safe_methods:
            return safe_wrapper

        raise AttributeError(f"'RollingGroupBy' object has no attribute '{name}'.")


class _SafeSeries:

    def __init__(self, series: Series) -> None:
        """"""
        self._series = series

    def __getattr__(self, name: str) -> '_SafeSeries':
        """"""
        _name = name.upper().replace('_', '')

        safe_methods = {# Methods
                        'ABS'                    : 'abs',
                        'ALIAS'                  : 'alias',
                        'ALL'                    : 'all',
                        'ANY'                    : 'any',
                        'APPROXNUNIQUE'          : 'approx_n_unique',
                        'ARCCOS'                 : 'arccos',
                        'ARCCOSH'                : 'arccosh',
                        'ARCSIN'                 : 'arcsin',
                        'ARCSINH'                : 'arcsinh',
                        'ARCTAN'                 : 'arctan',
                        'ARCTANH'                : 'arctanh',
                        'ARGMAX'                 : 'arg_max',
                        'ARGMIN'                 : 'arg_min',
                        'ARGSORT'                : 'arg_sort',
                        'ARGTRUE'                : 'arg_true',
                        'ARGUNIQUE'              : 'arg_unique',
                        'BACKWARDFILL'           : 'backward_fill',
                        'BITWISEAND'             : 'bitwise_and',
                        'BITWISECOUNTONES'       : 'bitwise_count_ones',
                        'BITWISECOUNTZEROS'      : 'bitwise_count_zeros',
                        'BITWISELEADINGONES'     : 'bitwise_leading_ones',
                        'BITWISELEADINGZEROS'    : 'bitwise_leading_zeros',
                        'BITWISEOR'              : 'bitwise_or',
                        'BITWISETRAILINGONES'    : 'bitwise_trailing_ones',
                        'BITWISETRAILINGZEROS'   : 'bitwise_trailing_zeros',
                        'BITWISEXOR'             : 'bitwise_xor',
                        'BOTTOMK'                : 'bottom_k',
                        'BOTTOMKBY'              : 'bottom_k_by',
                        'CAST'                   : 'cast',
                        'CBRT'                   : 'cbrt',
                        'CEIL'                   : 'ceil',
                        'CHUNKLENGTHS'           : 'chunk_lengths',
                        'CLEAR'                  : 'clear',
                        'CLIP'                   : 'clip',
                        'CLONE'                  : 'clone',
                        'COS'                    : 'cos',
                        'COSH'                   : 'cosh',
                        'COT'                    : 'cot',
                        'COUNT'                  : 'count',
                        'CUMCOUNT'               : 'cum_count',
                        'CUMMAX'                 : 'cum_max',
                        'CUMMIN'                 : 'cum_min',
                        'CUMPROD'                : 'cum_prod',
                        'CUMSUM'                 : 'cum_sum',
                        'CUMULATIVEEVAL'         : 'cumulative_eval',
                        'CUT'                    : 'cut',
                        'DESCRIBE'               : 'describe',
                        'DIFF'                   : 'diff',
                        'DOT'                    : 'dot',
                        'DROPNANS'               : 'drop_nans',
                        'DROPNULLS'              : 'drop_nulls',
                        'ENTROPY'                : 'entropy',
                        'EQ'                     : 'eq',
                        'EQMISSING'              : 'eq_missing',
                        'EQUALS'                 : 'equals',
                        'ESTIMATEDSIZE'          : 'estimated_size',
                        'EWMMEAN'                : 'ewm_mean',
                        'EWMMEANBY'              : 'ewm_mean_by',
                        'EWMSTD'                 : 'ewm_std',
                        'EWMVAR'                 : 'ewm_var',
                        'EXP'                    : 'exp',
                        'EXPLODE'                : 'explode',
                        'EXTENDCONSTANT'         : 'extend_constant',
                        'FILLNAN'                : 'fill_nan',
                        'FILLNULL'               : 'fill_null',
                        'FILTER'                 : 'filter',
                        'FIRST'                  : 'first',
                        'FLOOR'                  : 'floor',
                        'FORWARDFILL'            : 'forward_fill',
                        'GATHER'                 : 'gather',
                        'GATHEREVERY'            : 'gather_every',
                        'GE'                     : 'ge',
                        'GETCHUNKS'              : 'get_chunks',
                        'GT'                     : 'gt',
                        'HASNULLS'               : 'has_nulls',
                        'HASH'                   : 'hash',
                        'HEAD'                   : 'head',
                        'HIST'                   : 'hist',
                        'IMPLODE'                : 'implode',
                        'INDEXOF'                : 'index_of',
                        'INTERPOLATE'            : 'interpolate',
                        'INTERPOLATEBY'          : 'interpolate_by',
                        'ISBETWEEN'              : 'is_between',
                        'ISCLOSE'                : 'is_close',
                        'ISDUPLICATED'           : 'is_duplicated',
                        'ISEMPTY'                : 'is_empty',
                        'ISFINITE'               : 'is_finite',
                        'ISFIRSTDISTINCT'        : 'is_first_distinct',
                        'ISIN'                   : 'is_in',
                        'ISINFINITE'             : 'is_infinite',
                        'ISLASTDISTINCT'         : 'is_last_distinct',
                        'ISNAN'                  : 'is_nan',
                        'ISNOTNAN'               : 'is_not_nan',
                        'ISNOTNULL'              : 'is_not_null',
                        'ISNULL'                 : 'is_null',
                        'ISSORTED'               : 'is_sorted',
                        'ISUNIQUE'               : 'is_unique',
                        'ITEM'                   : 'item',
                        'KURTOSIS'               : 'kurtosis',
                        'LAST'                   : 'last',
                        'LE'                     : 'le',
                        'LEN'                    : 'len',
                        'LIMIT'                  : 'limit',
                        'LOG'                    : 'log',
                        'LOG10'                  : 'log10',
                        'LOG1P'                  : 'log1p',
                        'LOWERBOUND'             : 'lower_bound',
                        'LT'                     : 'lt',
                        'MAPELEMENTS'            : 'map_elements',
                        'MAX'                    : 'max',
                        'MEAN'                   : 'mean',
                        'MEDIAN'                 : 'median',
                        'MIN'                    : 'min',
                        'MODE'                   : 'mode',
                        'NCHUNKS'                : 'n_chunks',
                        'NUNIQUE'                : 'n_unique',
                        'NANMAX'                 : 'nan_max',
                        'NANMIN'                 : 'nan_min',
                        'NE'                     : 'ne',
                        'NEMISSING'              : 'ne_missing',
                        'NEWFROMINDEX'           : 'new_from_index',
                        'NOT'                    : 'not_',
                        'NULLCOUNT'              : 'null_count',
                        'PCTCHANGE'              : 'pct_change',
                        'PEAKMAX'                : 'peak_max',
                        'PEAKMIN'                : 'peak_min',
                        'POW'                    : 'pow',
                        'PRODUCT'                : 'product',
                        'QCUT'                   : 'qcut',
                        'QUANTILE'               : 'quantile',
                        'RANK'                   : 'rank',
                        'RECHUNK'                : 'rechunk',
                        'REINTERPRET'            : 'reinterpret',
                        'RENAME'                 : 'rename',
                        'REPEATBY'               : 'repeat_by',
                        'REPLACE'                : 'replace',
                        'REPLACESTRICT'          : 'replace_strict',
                        'RESHAPE'                : 'reshape',
                        'REVERSE'                : 'reverse',
                        'RLE'                    : 'rle',
                        'RLEID'                  : 'rle_id',
                        'ROLLINGKURTOSIS'        : 'rolling_kurtosis',
                        'ROLLINGMAP'             : 'rolling_map',
                        'ROLLINGMAX'             : 'rolling_max',
                        'ROLLINGMAXBY'           : 'rolling_max_by',
                        'ROLLINGMEAN'            : 'rolling_mean',
                        'ROLLINGMEANBY'          : 'rolling_mean_by',
                        'ROLLINGMEDIAN'          : 'rolling_median',
                        'ROLLINGMEDIANBY'        : 'rolling_median_by',
                        'ROLLINGMIN'             : 'rolling_min',
                        'ROLLINGMINBY'           : 'rolling_min_by',
                        'ROLLINGQUANTILE'        : 'rolling_quantile',
                        'ROLLINGQUANTILEBY'      : 'rolling_quantile_by',
                        'ROLLINGRANK'            : 'rolling_rank',
                        'ROLLINGRANKBY'          : 'rolling_rank_by',
                        'ROLLINGSKEW'            : 'rolling_skew',
                        'ROLLINGSTD'             : 'rolling_std',
                        'ROLLINGSTDBY'           : 'rolling_std_by',
                        'ROLLINGSUM'             : 'rolling_sum',
                        'ROLLINGSUMBY'           : 'rolling_sum_by',
                        'ROLLINGVAR'             : 'rolling_var',
                        'ROLLINGVARBY'           : 'rolling_var_by',
                        'ROUND'                  : 'round',
                        'ROUNDSIGFIGS'           : 'round_sig_figs',
                        'SAMPLE'                 : 'sample',
                        'SCATTER'                : 'scatter',
                        'SEARCHSORTED'           : 'search_sorted',
                        'SET'                    : 'set',
                        'SETSORTED'              : 'set_sorted',
                        'SHIFT'                  : 'shift',
                        'SHRINKDTYPE'            : 'shrink_dtype',
                        'SHRINKTOFIT'            : 'shrink_to_fit',
                        'SHUFFLE'                : 'shuffle',
                        'SIGN'                   : 'sign',
                        'SIN'                    : 'sin',
                        'SINH'                   : 'sinh',
                        'SKEW'                   : 'skew',
                        'SLICE'                  : 'slice',
                        'SORT'                   : 'sort',
                        'SQRT'                   : 'sqrt',
                        'STD'                    : 'std',
                        'SUM'                    : 'sum',
                        'TAIL'                   : 'tail',
                        'TAN'                    : 'tan',
                        'TANH'                   : 'tanh',
                        'TODUMMIES'              : 'to_dummies',
                        'TOFRAME'                : 'to_frame',
                        'TOINITREPR'             : 'to_init_repr',
                        'TOLIST'                 : 'to_list',
                        'TOPHYSICAL'             : 'to_physical',
                        'TOPK'                   : 'top_k',
                        'TOPKBY'                 : 'top_k_by',
                        'UNIQUE'                 : 'unique',
                        'UNIQUECOUNTS'           : 'unique_counts',
                        'UPPERBOUND'             : 'upper_bound',
                        'VALUECOUNTS'            : 'value_counts',
                        'VAR'                    : 'var',
                        'ZIPWITH'                : 'zip_with',

                        # Attributes
                        'DTYPE'                  : 'dtype',
                        'NAME'                   : 'name',
                        'SHAPE'                  : 'shape',

                        # arr.
                        'AGG'                    : 'agg',
                        'ALL'                    : 'all',
                        'ANY'                    : 'any',
                        'ARGMAX'                 : 'arg_max',
                        'ARGMIN'                 : 'arg_min',
                        'CONTAINS'               : 'contains',
                        'COUNTMATCHES'           : 'count_matches',
                        'EXPLODE'                : 'explode',
                        'EVAL'                   : 'eval',
                        'FIRST'                  : 'first',
                        'GET'                    : 'get',
                        'JOIN'                   : 'join',
                        'LAST'                   : 'last',
                        'LEN'                    : 'len',
                        'MAX'                    : 'max',
                        'MEDIAN'                 : 'median',
                        'MIN'                    : 'min',
                        'NUNIQUE'                : 'n_unique',
                        'REVERSE'                : 'reverse',
                        'SHIFT'                  : 'shift',
                        'SORT'                   : 'sort',
                        'STD'                    : 'std',
                        'SUM'                    : 'sum',
                        'TOLIST'                 : 'to_list',
                        'TOSTRUCT'               : 'to_struct',
                        'UNIQUE'                 : 'unique',
                        'VAR'                    : 'var',

                        # bin.
                        'CONTAINS'               : 'contains',
                        'DECODE'                 : 'decode',
                        'ENCODE'                 : 'encode',
                        'ENDSWITH'               : 'ends_with',
                        'REINTERPRET'            : 'reinterpret',
                        'SIZE'                   : 'size',
                        'STARTSWITH'             : 'starts_with',

                        # cat.
                        'ENDSWITH'               : 'ends_with',
                        'GETCATEGORIES'          : 'get_categories',
                        'ISLOCAL'                : 'is_local',
                        'LENBYTES'               : 'len_bytes',
                        'LENCHARS'               : 'len_chars',
                        'STARTSWITH'             : 'starts_with',
                        'TOLOCAL'                : 'to_local',

                        # dt.
                        'ADDBUSINESSDAYS'        : 'add_business_days',
                        'BASEUTCOFFSET'          : 'base_utc_offset',
                        'CASTTIMEUNIT'           : 'cast_time_unit',
                        'CENTURY'                : 'century',
                        'COMBINE'                : 'combine',
                        'CONVERTTIMEZONE'        : 'convert_time_zone',
                        'DATE'                   : 'date',
                        'DATETIME'               : 'datetime',
                        'DAY'                    : 'day',
                        'DAYSINMONTH'            : 'days_in_month',
                        'DSTOFFSET'              : 'dst_offset',
                        'EPOCH'                  : 'epoch',
                        'HOUR'                   : 'hour',
                        'ISBUSINESSDAY'          : 'is_business_day',
                        'ISLEAPYEAR'             : 'is_leap_year',
                        'ISOYEAR'                : 'iso_year',
                        'MAX'                    : 'max',
                        'MEAN'                   : 'mean',
                        'MEDIAN'                 : 'median',
                        'MICROSECOND'            : 'microsecond',
                        'MILLENNIUM'             : 'millennium',
                        'MILLISECOND'            : 'millisecond',
                        'MIN'                    : 'min',
                        'MINUTE'                 : 'minute',
                        'MONTH'                  : 'month',
                        'MONTHEND'               : 'month_end',
                        'MONTHSTART'             : 'month_start',
                        'NANOSECOND'             : 'nanosecond',
                        'OFFSETBY'               : 'offset_by',
                        'ORDINALDAY'             : 'ordinal_day',
                        'QUARTER'                : 'quarter',
                        'REPLACE'                : 'replace',
                        'REPLACETIMEZONE'        : 'replace_time_zone',
                        'ROUND'                  : 'round',
                        'SECOND'                 : 'second',
                        'STRFTIME'               : 'strftime',
                        'TIME'                   : 'time',
                        'TIMESTAMP'              : 'timestamp',
                        'TOSTRING'               : 'to_string',
                        'TOTALDAYS'              : 'total_days',
                        'TOTALHOURS'             : 'total_hours',
                        'TOTALMICROSECONDS'      : 'total_microseconds',
                        'TOTALMILLISECONDS'      : 'total_milliseconds',
                        'TOTALMINUTES'           : 'total_minutes',
                        'TOTALNANOSECONDS'       : 'total_nanoseconds',
                        'TOTALSECONDS'           : 'total_seconds',
                        'TRUNCATE'               : 'truncate',
                        'WEEK'                   : 'week',
                        'WEEKDAY'                : 'weekday',
                        'WITHTIMEUNIT'           : 'with_time_unit',
                        'YEAR'                   : 'year',

                        # list.
                        'AGG'                    : 'agg',
                        'ALL'                    : 'all',
                        'ANY'                    : 'any',
                        'ARGMAX'                 : 'arg_max',
                        'ARGMIN'                 : 'arg_min',
                        'CONCAT'                 : 'concat',
                        'CONTAINS'               : 'contains',
                        'COUNTMATCHES'           : 'count_matches',
                        'DIFF'                   : 'diff',
                        'DROPNULLS'              : 'drop_nulls',
                        'EVAL'                   : 'eval',
                        'EXPLODE'                : 'explode',
                        'FILTER'                 : 'filter',
                        'FIRST'                  : 'first',
                        'GATHER'                 : 'gather',
                        'GATHEREVERY'            : 'gather_every',
                        'GET'                    : 'get',
                        'HEAD'                   : 'head',
                        'ITEM'                   : 'item',
                        'JOIN'                   : 'join',
                        'LAST'                   : 'last',
                        'LEN'                    : 'len',
                        'MAX'                    : 'max',
                        'MEAN'                   : 'mean',
                        'MEDIAN'                 : 'median',
                        'MIN'                    : 'min',
                        'NUNIQUE'                : 'n_unique',
                        'REVERSE'                : 'reverse',
                        'SAMPLE'                 : 'sample',
                        'SETDIFFERENCE'          : 'set_difference',
                        'SETINTERSECTION'        : 'set_intersection',
                        'SETSYMMETRICDIFFERENCE' : 'set_symmetric_difference',
                        'SETUNION'               : 'set_union',
                        'SHIFT'                  : 'shift',
                        'SLICE'                  : 'slice',
                        'SORT'                   : 'sort',
                        'STD'                    : 'std',
                        'SUM'                    : 'sum',
                        'TAIL'                   : 'tail',
                        'TOARRAY'                : 'to_array',
                        'TOSTRUCT'               : 'to_struct',
                        'UNIQUE'                 : 'unique',
                        'VAR'                    : 'var',

                        # str.
                        'CONCAT'                 : 'concat',
                        'CONTAINS'               : 'contains',
                        'CONTAINSANY'            : 'contains_any',
                        'COUNTMATCHES'           : 'count_matches',
                        'DECODE'                 : 'decode',
                        'ENCODE'                 : 'encode',
                        'ENDSWITH'               : 'ends_with',
                        'ESCAPEREGEX'            : 'escape_regex',
                        'EXPLODE'                : 'explode',
                        'EXTRACT'                : 'extract',
                        'EXTRACTALL'             : 'extract_all',
                        'EXTRACTGROUPS'          : 'extract_groups',
                        'EXTRACTMANY'            : 'extract_many',
                        'FIND'                   : 'find',
                        'FINDMANY'               : 'find_many',
                        'HEAD'                   : 'head',
                        'JOIN'                   : 'join',
                        'JSONDECODE'             : 'json_decode',
                        'JSONPATHMATCH'          : 'json_path_match',
                        'LENBYTES'               : 'len_bytes',
                        'LENCHARS'               : 'len_chars',
                        'NORMALIZE'              : 'normalize',
                        'PADEND'                 : 'pad_end',
                        'PADSTART'               : 'pad_start',
                        'REPLACE'                : 'replace',
                        'REPLACEALL'             : 'replace_all',
                        'REPLACEMANY'            : 'replace_many',
                        'REVERSE'                : 'reverse',
                        'SLICE'                  : 'slice',
                        'SPLIT'                  : 'split',
                        'SPLITEXACT'             : 'split_exact',
                        'SPLITN'                 : 'splitn',
                        'STARTSWITH'             : 'starts_with',
                        'STRIPCHARS'             : 'strip_chars',
                        'STRIPCHARSSTART'        : 'strip_chars_start',
                        'STRIPCHARSEND'          : 'strip_chars_end',
                        'STRIPPREFIX'            : 'strip_prefix',
                        'STRIPSUFFIX'            : 'strip_suffix',
                        'STRPTIME'               : 'strptime',
                        'TAIL'                   : 'tail',
                        'TODATE'                 : 'to_date',
                        'TODATETIME'             : 'to_datetime',
                        'TODECIMAL'              : 'to_decimal',
                        'TOINTEGER'              : 'to_integer',
                        'TOLOWERCASE'            : 'to_lowercase',
                        'TOTIME'                 : 'to_time',
                        'TOTITLECASE'            : 'to_titlecase',
                        'TOUPPERCASE'            : 'to_uppercase',
                        'ZFILL'                  : 'zfill',

                        # struct.
                        'FIELD'                  : 'field',
                        'UNNEST'                 : 'unnest',
                        'JSONENCODE'             : 'json_encode',
                        'RENAMEFIELDS'           : 'rename_fields',
                        'FIELDS'                 : 'fields',
                        'SCHEMA'                 : 'schema'}

        safe_namespaces = {'ARR'    : 'arr',
                           'BIN'    : 'bin',
                           'CAT'    : 'cat',
                           'DT'     : 'dt',
                           'LIST'   : 'list',
                           'STR'    : 'str',
                           'STRUCT' : 'struct'}

        def safe_wrapper(*args, **kwargs):
            """"""
            args = list(args)
            for idx, arg in enumerate(args):
                if isinstance(arg, _SafeExpression):
                    args[idx] = arg._expression
            for key, value in kwargs:
                if isinstance(value, _SafeExpression):
                    kwargs[key] = value._expression
            name = safe_methods[_name]
            method = getattr(self._series, name)
            result = method(*args, **kwargs)
            if isinstance(result, Series):
                return _SafeSeries(result)
            return result

        if _name in safe_methods:
            return safe_wrapper

        if _name in safe_namespaces:
            name = safe_namespaces[_name]
            result = getattr(self._series, name)
            return _SafeExpression(result)


        raise AttributeError(f"'Series' object has no attribute '{name}'.")


class _SafeDataFrame:

    def __init__(self, dataframe: DataFrame) -> None:
        """"""
        self._dataframe = dataframe

    def __getattr__(self, name: str) -> '_SafeDataFrame':
        """"""
        _name = name.upper().replace('_', '')

        safe_methods = {# Methods
                        'BOTTOMK'        : 'bottom_k',
                        'CAST'           : 'cast',
                        'CLEAR'          : 'clear',
                        'CLONE'          : 'clone',
                        'CORR'           : 'corr',
                        'COUNT'          : 'count',
                        'DESCRIBE'       : 'describe',
                        'DROP'           : 'drop',
                        'DROPNANS'       : 'drop_nans',
                        'DROPNULLS'      : 'drop_nulls',
                        'EQUALS'         : 'equals',
                        'ESTIMATEDSIZE'  : 'estimated_size',
                        'EXPLODE'        : 'explode',
                        'FILLNAN'        : 'fill_nan',
                        'FILLNULL'       : 'fill_null',
                        'FILTER'         : 'filter',
                        'FOLD'           : 'fold',
                        'GATHEREVERY'    : 'gather_every',
                        'GETCOLUMN'      : 'get_column',
                        'GETCOLUMNINDEX' : 'get_column_index',
                        'GETCOLUMNS'     : 'get_columns',
                        'GROUPBY'        : 'group_by',
                        'GROUPBYDYNAMIC' : 'group_by_dynamic',
                        'HASHROWS'       : 'hash_rows',
                        'HEAD'           : 'head',
                        'HSTACK'         : 'hstack',
                        'INSERTCOLUMN'   : 'insert_column',
                        'INTERPOLATE'    : 'interpolate',
                        'ISDUPLICATED'   : 'is_duplicated',
                        'ISEMPTY'        : 'is_empty',
                        'ISUNIQUE'       : 'is_unique',
                        'ITEM'           : 'item',
                        'ITERCOLUMNS'    : 'iter_columns',
                        'ITERROWS'       : 'iter_rows',
                        'ITERSLICES'     : 'iter_slices',
                        'JOIN'           : 'join',
                        'JOINASOF'       : 'join_asof',
                        'JOINWHERE'      : 'join_where',
                        'LIMIT'          : 'limit',
                        'MAPCOLUMNS'     : 'map_columns',
                        'MAPROWS'        : 'map_rows',
                        'MATCHTOSCHEMA'  : 'match_to_schema',
                        'MAX'            : 'max',
                        'MAXHORIZONTAL'  : 'max_horizontal',
                        'MEAN'           : 'mean',
                        'MEANHORIZONTAL' : 'mean_horizontal',
                        'MEDIAN'         : 'median',
                        'MERGESORTED'    : 'merge_sorted',
                        'MIN'            : 'min',
                        'MINHORIZONTAL'  : 'min_horizontal',
                        'NCHUNKS'        : 'n_chunks',
                        'NUNIQUE'        : 'n_unique',
                        'NULLCOUNT'      : 'null_count',
                        'PARTITIONBY'    : 'partition_by',
                        'PIPE'           : 'pipe',
                        'PIVOT'          : 'pivot',
                        'PRODUCT'        : 'product',
                        'QUANTILE'       : 'quantile',
                        'RECHUNK'        : 'rechunk',
                        'REMOVE'         : 'remove',
                        'RENAME'         : 'rename',
                        'REPLACECOLUMN'  : 'replace_column',
                        'REVERSE'        : 'reverse',
                        'ROLLING'        : 'rolling',
                        'ROW'            : 'row',
                        'ROWS'           : 'rows',
                        'ROWSBYKEY'      : 'rows_by_key',
                        'SAMPLE'         : 'sample',
                        'SELECT'         : 'select',
                        'SELECTSEQ'      : 'select_seq',
                        'SETSORTED'      : 'set_sorted',
                        'SHIFT'          : 'shift',
                        'SHRINKTOFIT'    : 'shrink_to_fit',
                        'SLICE'          : 'slice',
                        'SORT'           : 'sort',
                        'SQL'            : 'sql',
                        'STD'            : 'std',
                        'SUM'            : 'sum',
                        'SUMHORIZONTAL'  : 'sum_horizontal',
                        'TAIL'           : 'tail',
                        'TODICTS'        : 'to_dicts',
                        'TODICT'         : 'to_dict',
                        'TODUMMIES'      : 'to_dummies',
                        'TOINITREPR'     : 'to_init_repr',
                        'TOSERIES'       : 'to_series',
                        'TOSTRUCT'       : 'to_struct',
                        'TOPK'           : 'top_k',
                        'TRANSPOSE'      : 'transpose',
                        'UNIQUE'         : 'unique',
                        'UNNEST'         : 'unnest',
                        'UNPIVOT'        : 'unpivot',
                        'UNSTACK'        : 'unstack',
                        'UPDATE'         : 'update',
                        'UPSAMPLE'       : 'upsample',
                        'VAR'            : 'var',
                        'VSTACK'         : 'vstack',
                        'WITHCOLUMNS'    : 'with_columns',
                        'WITHCOLUMNSSEQ' : 'with_columns_seq',
                        'WITHROWINDEX'   : 'with_row_index',

                        # Attributes
                        'COLUMNS'        : 'columns',
                        'DTYPES'         : 'dtypes',
                        'HEIGHT'         : 'height',
                        'SCHEMA'         : 'schema',
                        'SHAPE'          : 'shape',
                        'WIDTH'          : 'width'}

        def safe_wrapper(*args, **kwargs):
            """"""
            args = list(args)
            for idx, arg in enumerate(args):
                if isinstance(arg, _SafeExpression):
                    args[idx] = arg._expression
            for key, value in kwargs:
                if isinstance(value, _SafeExpression):
                    kwargs[key] = value._expression

            name = safe_methods[_name]
            method = getattr(self._dataframe, name)
            result = method(*args, **kwargs)

            if isinstance(result, DataFrame):
                return _SafeDataFrame(result)
            if isinstance(result, DynamicGroupBy):
                return _SafeDynamicGroupBy(result)
            if isinstance(result, GroupBy):
                return _SafeGroupBy(result)
            if isinstance(result, RollingGroupBy):
                return _SafeRollingGroupBy(result)
            if isinstance(result, Series):
                return _SafeSeries(result)
            return result

        if _name in safe_methods:
            return safe_wrapper

        raise AttributeError(f"'DataFrame' object has no attribute '{name}'.")


class _NormDatetime(datetime):

    @classmethod
    def __getattr__(cls, name: str) -> datetime:
        """"""
        name = name.lower()
        if hasattr(datetime, name):
            return getattr(datetime, name)
        raise AttributeError(f"'datetime' object has no attribute '{name}'.")

    def __getattr__(self, name: str) -> '_NormDatetime':
        """"""
        name = name.lower()
        if hasattr(datetime, name):
            return getattr(self, name)
        raise AttributeError(f"'datetime' object has no attribute '{name}'.")


class _NormDate(date):

    @classmethod
    def __getattr__(cls, name: str) -> date:
        """"""
        name = name.lower()
        if hasattr(date, name):
            return getattr(date, name)
        raise AttributeError(f"'date' object has no attribute '{name}'.")

    def __getattr__(self, name: str) -> '_NormDate':
        """"""
        name = name.lower()
        if hasattr(date, name):
            return getattr(self, name)
        raise AttributeError(f"'date' object has no attribute '{name}'.")


class _NormTime(time):

    @classmethod
    def __getattr__(cls, name: str) -> time:
        """"""
        name = name.lower()
        if hasattr(time, name):
            return getattr(time, name)
        raise AttributeError(f"'time' object has no attribute '{name}'.")

    def __getattr__(self, name: str) -> '_NormTime':
        """"""
        name = name.lower()
        if hasattr(time, name):
            return getattr(self, name)
        raise AttributeError(f"'time' object has no attribute '{name}'.")


@v_args(inline=True)
class Transformer(Transformer):

    OPERATORS = {"+"  : operator.add,
                 "-"  : operator.sub,
                 "*"  : operator.mul,
                 "/"  : operator.truediv,
                 "//" : operator.floordiv,
                 "%"  : operator.mod,
                 "**" : operator.pow,
                 "^"  : operator.xor,
                 "&"  : operator.and_,
                 "|"  : operator.or_,

                 ">"  : operator.gt,
                 "<"  : operator.lt,
                 "==" : operator.eq,
                 "!=" : operator.ne,
                 ">=" : operator.ge,
                 "<=" : operator.le}

    POLARS_OPERATORS = {'+'  : 'add',
                        '-'  : 'sub',
                        '*'  : 'mul',
                        '/'  : 'truediv',
                        '//' : 'floordiv',
                        '%'  : 'mod',
                        '**' : 'pow',
                        '^'  : 'xor',
                        '&'  : 'and',
                        '|'  : 'or',

                        '>'  : 'gt',
                        '<'  : 'lt',
                        '==' : 'eq',
                        '!=' : 'ne',
                        '>=' : 'ge',
                        '<=' : 'le'}

    def __init__(self,
                 vars:   dict,
                 tables: dict[str, DataFrame]):
        """"""
        super().__init__()

        # TODO: implement https://docs.pola.rs/api/python/dev/reference/functions.html
        # TODO: implement https://docs.pola.rs/api/python/dev/reference/selectors.html
        self.vars = {'EXPRESSION' : _SafeExpression,
                     'ALLCOLUMNS' : _SafeExpression.ALLCOLUMNS,
                     'COLUMN'     : _SafeExpression.COLUMN,
                     'DATETIME'   : _NormDatetime,
                     'DATE'       : _NormDate,
#                    'SELECTOR'   : _SafeSelector,
                     'SERIES'     : _SafeSeries,
                     'TABLE'      : self.get_table,
                     'TIME'       : _NormTime,
                     'TYPE'       : _SafeDataType}

        self.vars.update(vars)

        self.tables = {}
        for tname, table in tables.items():
            tpath = parse_table_rpath(tname)
            self.tables[tpath] = table

    def collect(self, result):
        """"""
        # TODO: implement _SafeLazyFrame
        if isinstance(result, _SafeGroupBy):
            return result._groupby
        if isinstance(result, _SafeDynamicGroupBy):
            return result._groupby
        if isinstance(result, _SafeRollingGroupBy):
            return result._groupby
        if isinstance(result, _SafeSeries):
            return result._series
        if isinstance(result, _SafeDataFrame):
            return result._dataframe
        if isinstance(result, _SafeExpression):
            return result._expression
        return result

    def get_table(self, *args, **kwargs):
        """"""
        if len(args) == 1 and isinstance(args[0], str):
            tpath = parse_table_rpath(args[0])
            table = self.tables.get(tpath)
            if isinstance(table, DataFrame):
                return _SafeDataFrame(table)
            return None
        return _SafeDataFrame(DataFrame(*args, **kwargs))

    def single_line(self, arg):
        """"""
        return arg

    def multi_line(self, arg):
        """"""
        return arg

    def script(self, *args):
        """"""
        if args:
            return args[-1]
        return None

    def assignment(self, *args):
        """"""
        token, value = args
        if isinstance(value, Token):
            value = self.vars[value.value]
        var = str(token.value)
        self.vars[var] = value
        return value

    def _bitwise(self, *args):
        """"""
        left = args[0]
        for i in range(1, len(args), 2):
            op_str = str(args[i])
            right = args[i+1]
            if isinstance(left, Token):
                left = self.vars[left.value]
            if isinstance(right, Token):
                right = self.vars[right.value]
            if isinstance(left, _SafeExpression):
                op = self.POLARS_OPERATORS[op_str]
                left = getattr(left, op)(right)
                continue
            if isinstance(right, _SafeExpression):
                op = self.POLARS_OPERATORS[op_str]
                if not isinstance(left, _SafeExpression):
                    from polars import lit
                    left = _SafeExpression(lit(left))
                left = getattr(left, op)(right)
                continue
            op = self.OPERATORS[op_str]
            left = op(left, right)
        return left

    bitwise_or  = _bitwise
    bitwise_xor = _bitwise
    bitwise_and = _bitwise
    comparison  = _bitwise
    summation   = _bitwise
    product     = _bitwise

    def exponent(self, *args):
        """"""
        if len(args) == 1:
            return args[0]
        left, op, right = args
        op = self.OPERATORS[str(op)]
        return op(left, right)

    def unary(self, *args):
        """"""
        if len(args) == 1:
            return args[0]
        token, value = args
        op = str(token).lower()
        if op in {'~', '-'}:
            if isinstance(value, _SafeExpression):
                return value.neg()
            return operator.neg(value)
        if op == 'not':
            return operator.not_(value)
        return value

    def atom(self, *args):
        """"""
        obj = args[0]
        if isinstance(obj, Token):
            name = obj.value
            if var := self.vars.get(name):
                obj = var
            else:
                name = name.upper()
                obj = self.vars.get(name, obj)
        for arg in args[1:]:
            if isinstance(arg, tuple):
                _args, _kwargs = arg
                for idx, arg in enumerate(_args):
                    if isinstance(arg, Token):
                        _args[idx] = self.vars[arg.value]
                for key, arg in _kwargs:
                    if isinstance(arg, Token):
                        _kwargs[key] = self.vars[arg.value]
                obj = obj(*_args, **_kwargs)
            else:
                obj = getattr(obj, arg)
        return obj

    def call(self, arg):
        """"""
        return arg if arg else ([], {})

    def primary(self, arg):
        """"""
        if not isinstance(arg, Token):
            return arg
        if var := self.vars.get(arg):
            return var
        arg = arg.upper()
        return self.vars.get(arg, arg)

    def tuple(self, *args):
        """"""
        return tuple(args)

    def list(self, *args):
        """"""
        return list(args)

    def dict(self, *args):
        """"""
        return dict(args)

    def pair(self, *args):
        """"""
        return args

    def table(self, arg):
        """"""
        return self.get_table(arg)

    def column(self, arg):
        """"""
        return _SafeExpression.COLUMN(arg)

    def arguments(self, *args):
        """"""
        _args = []
        _kwargs = {}
        for arg in args:
            if isinstance(arg, tuple):
                _kwargs[arg[0]] = arg[1]
            else:
                _args.append(arg)
        return (_args, _kwargs)

    def argument(self, arg):
        """"""
        return arg

    def pair_argument(self, *args):
        """"""
        return args

    def NAME(self, value: str):
        """"""
        return value

    def NUMBER(self, value: str):
        """"""
        try:
            return int(value)
        except:
            return float(value)

    def STRING(self, value: str):
        """"""
        if value.startswith('"'):
            from json import loads
            return loads(value)
        else:
            return value[1:-1].replace(r"\'", "'") \
                              .replace(r"\\", "\\")


parser = Lark(_GRAMMAR, parser = 'lalr')
