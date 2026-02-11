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
from datetime import datetime
from datetime import date
from datetime import time
from difflib import get_close_matches
from typing import Any
import json
import operator
import polars
import polars.selectors

# TODO: add support for basic programming syntaxes
# TODO: add support for python-like basic syntaxes

_GRAMMAR = r"""
    ?start: script

    ?script:    (NEWLINE* assignment)* NEWLINE* formula [NEWLINE*]
    assignment: NAME "=" formula

    ?formula:     bitwise_or
    ?bitwise_or:  bitwise_xor (BITWISE_OR  bitwise_xor)*
    ?bitwise_xor: bitwise_and (BITWISE_XOR bitwise_and)*
    ?bitwise_and: comparison  (BITWISE_AND comparison)*

    ?comparison: summation (COMPARATOR summation)*
    ?summation:  product   (SUMMATOR   product)*
    ?product:    exponent  (PRODUCTOR  exponent)*
    ?exponent:   unary     (EXPONENTOR exponent)?

    ?unary: UNATOR unary | atom

    atom: primary (call | "." NAME call?)*
    call: "(" [arguments] ")"

    ?primary: "(" formula ")"
            | tuple
            | list
            | dict
            | NUMBER
            | STRING
            | VAR
            | NAME

    tuple: "(" [formula ("," formula?)+ [","]] ")"
    list:  "[" [formula ("," formula)* [","]] "]"
    dict:  "{" [pair ("," pair)* [","]] "}"
    pair:  (STRING | NUMBER | tuple) ":" formula

    arguments: argument ("," argument)* [","]
    argument:  (formula | pair_arg)
    pair_arg:  NAME "=" formula

    COMPARATOR: ">" | "<" | "==" | "!=" | ">=" | "<="
    SUMMATOR:   "+" | "-"
    PRODUCTOR:  "*" | "/" | "//" | "%"
    EXPONENTOR: "**"
    UNATOR:     "~" | "not"

    BITWISE_OR:  "|"
    BITWISE_XOR: "^"
    BITWISE_AND: "&"

    NAME: /[a-zA-Z_$][a-zA-Z0-9_$]*/

    VAR: "$" STRING

    %import common.NEWLINE
    %import common.WS_INLINE

    %ignore WS_INLINE
    %ignore NEWLINE

    %import common.SIGNED_NUMBER -> NUMBER
    %import common.ESCAPED_STRING

    STRING: ESCAPED_STRING | SINGLE_QUOTED_STRING
    SINGLE_QUOTED_STRING: /'(\\.|[^'\\])*'/
"""


class _AttrProxyMeta(type):
    def __getattr__(cls, name):
        return cls._getattr(name)


class _AttrProxy(metaclass = _AttrProxyMeta):

    _attributes: dict[str, Any] = {}

    def __getattr__(self, name):
        """"""
        return self._getattr(name)

    @classmethod
    def _getattr(cls, name):
        """"""
        if name in cls._attributes:
            return cls._attributes[name]

        matches = get_close_matches(name, cls._attributes.keys(), n=1)
        if matches:
            raise AttributeError(
                f"'{cls.__name__}' has no attribute '{name}'. "
                f"Did you mean: '{matches[0]}'?"
            )

        raise AttributeError(
            f"'{cls.__name__}' has no attribute '{name}'."
        )


class _PolarsType(_AttrProxy):

    _attributes = {
        'Array':       polars.Array,
        'Binary':      polars.Binary,
        'Boolean':     polars.Boolean,
        'Categorical': polars.Categorical,
        'Categories':  polars.Categories,
        'Date':        polars.Date,
        'DateTime':    polars.Datetime,
        'Decimal':     polars.Decimal,
        'Duration':    polars.Duration,
        'Enum':        polars.Enum,
        'Field':       polars.Field,
        'Float16':     polars.Float16,
        'Float32':     polars.Float32,
        'Float64':     polars.Float64,
        'Int128':      polars.Int128,
        'Int16':       polars.Int16,
        'Int32':       polars.Int32,
        'Int64':       polars.Int64,
        'Int8':        polars.Int8,
        'List':        polars.List,
        'Null':        polars.Null,
        'Object':      polars.Object,
        'String':      polars.String,
        'Struct':      polars.Struct,
        'Time':        polars.Time,
        'UInt16':      polars.UInt16,
        'UInt32':      polars.UInt32,
        'UInt64':      polars.UInt64,
        'UInt8':       polars.UInt8,
        'Unknown':     polars.Unknown,
        'Utf8':        polars.Utf8,
    }


class _PolarsSource(_AttrProxy):

    _attributes = {
        'read_avro':             polars.read_avro,
        'read_clipboard':        polars.read_clipboard,
        'read_csv':              polars.read_csv,
        'scan_csv':              polars.scan_csv,
        'read_database':         polars.read_database,
        'read_database_uri':     polars.read_database_uri,
        'read_delta':            polars.read_delta,
        'scan_delta':            polars.scan_delta,
        'read_excel':            polars.read_excel,
        'read_ods':              polars.read_ods,
        'read_ipc':              polars.read_ipc,
        'read_ipc_schema':       polars.read_ipc_schema,
        'read_ipc_stream':       polars.read_ipc_stream,
        'scan_ipc':              polars.scan_ipc,
        'scan_iceberg':          polars.scan_iceberg,
        'read_json':             polars.read_json,
        'read_ndjson':           polars.read_ndjson,
        'scan_ndjson':           polars.scan_ndjson,
        'read_parquet':          polars.read_parquet,
        'read_parquet_metadata': polars.read_parquet_metadata,
        'read_parquet_schema':   polars.read_parquet_schema,
        'scan_parquet':          polars.scan_parquet,
    }


class _PolarsSelector(_AttrProxy):

    _attributes = {
        'all':              polars.selectors.all,
        'alpha':            polars.selectors.alpha,
        'alphanumeric':     polars.selectors.alphanumeric,
        'array':            polars.selectors.array,
        'binary':           polars.selectors.binary,
        'boolean':          polars.selectors.boolean,
        'by_dtype':         polars.selectors.by_dtype,
        'by_index':         polars.selectors.by_index,
        'by_name':          polars.selectors.by_name,
        'categorical':      polars.selectors.categorical,
        'contains':         polars.selectors.contains,
        'date':             polars.selectors.date,
        'datetime':         polars.selectors.datetime,
        'decimal':          polars.selectors.decimal,
        'digit':            polars.selectors.digit,
        'duration':         polars.selectors.duration,
        'ends_with':        polars.selectors.ends_with,
        'enum':             polars.selectors.enum,
        'exclude':          polars.selectors.exclude,
        'expand_selector':  polars.selectors.expand_selector,
        'first':            polars.selectors.first,
        'float':            polars.selectors.float,
        'integer':          polars.selectors.integer,
        'is_selector':      polars.selectors.is_selector,
        'last':             polars.selectors.last,
        'list':             polars.selectors.list,
        'matches':          polars.selectors.matches,
        'nested':           polars.selectors.nested,
        'numeric':          polars.selectors.numeric,
        'signed_integer':   polars.selectors.signed_integer,
        'starts_with':      polars.selectors.starts_with,
        'string':           polars.selectors.string,
        'struct':           polars.selectors.struct,
        'temporal':         polars.selectors.temporal,
        'time':             polars.selectors.time,
        'unsigned_integer': polars.selectors.unsigned_integer,
    }


class _PolarsUtility(_AttrProxy):

    _attributes = {
        'all':                polars.all,
        'all_horizontal':     polars.all_horizontal,
        'any':                polars.any,
        'any_horizontal':     polars.any_horizontal,
        'approx_n_unique':    polars.approx_n_unique,
        'arange':             polars.arange,
        'arctan2':            polars.arctan2,
        'arg_sort_by':        polars.arg_sort_by,
        'arg_where':          polars.arg_where,
        'business_day_count': polars.business_day_count,
        'coalesce':           polars.coalesce,
        'concat_arr':         polars.concat_arr,
        'concat_list':        polars.concat_list,
        'concat_str':         polars.concat_str,
        'corr':               polars.corr,
        'count':              polars.count,
        'cov':                polars.cov,
        'cum_count':          polars.cum_count,
        'cum_fold':           polars.cum_fold,
        'cum_reduce':         polars.cum_reduce,
        'cum_sum':            polars.cum_sum,
        'cum_sum_horizontal': polars.cum_sum_horizontal,
        'date':               polars.date,
        'date_range':         polars.date_range,
        'date_ranges':        polars.date_ranges,
        'datetime':           polars.datetime,
        'datetime_range':     polars.datetime_range,
        'datetime_ranges':    polars.datetime_ranges,
        'duration':           polars.duration,
        'element':            polars.element,
        'exclude':            polars.exclude,
        'field':              polars.field,
        'first':              polars.first,
        'fold':               polars.fold,
        'format':             polars.format,
        'from_epoch':         polars.from_epoch,
        'groups':             polars.groups,
        'head':               polars.head,
        'implode':            polars.implode,
        'int_range':          polars.int_range,
        'int_ranges':         polars.int_ranges,
        'last':               polars.last,
        'len':                polars.len,
        'linear_space':       polars.linear_space,
        'linear_spaces':      polars.linear_spaces,
        'lit':                polars.lit,
        'map_batches':        polars.map_batches,
        'map_groups':         polars.map_groups,
        'max':                polars.max,
        'max_horizontal':     polars.max_horizontal,
        'mean':               polars.mean,
        'mean_horizontal':    polars.mean_horizontal,
        'median':             polars.median,
        'min':                polars.min,
        'min_horizontal':     polars.min_horizontal,
        'n_unique':           polars.n_unique,
        'nth':                polars.nth,
        'ones':               polars.ones,
        'quantile':           polars.quantile,
        'reduce':             polars.reduce,
        'repeat':             polars.repeat,
        'rolling_corr':       polars.rolling_corr,
        'rolling_cov':        polars.rolling_cov,
        'row_index':          polars.row_index,
        'select':             polars.select,
        'sql':                polars.sql,
        'sql_expr':           polars.sql_expr,
        'std':                polars.std,
        'struct':             polars.struct,
        'sum':                polars.sum,
        'sum_horizontal':     polars.sum_horizontal,
        'tail':               polars.tail,
        'time':               polars.time,
        'time_range':         polars.time_range,
        'time_ranges':        polars.time_ranges,
        'var':                polars.var,
        'when':               polars.when,
        'zeros':              polars.zeros,

        'align_frames':       polars.align_frames,
        'concat':             polars.concat,
        'union':              polars.union,
        'defer':              polars.defer,

        'collect_all':        polars.collect_all,
        'explain_all':        polars.explain_all,

        'escape_regex':       polars.escape_regex,
    }


@v_args(inline = True)
class Transformer(Transformer):

    OPERATORS = {'+':  operator.add,
                 '-':  operator.sub,
                 '*':  operator.mul,
                 '/':  operator.truediv,
                 '//': operator.floordiv,
                 '%':  operator.mod,
                 '**': operator.pow,
                 '^':  operator.xor,
                 '&':  operator.and_,
                 '|':  operator.or_,

                 '>':  operator.gt,
                 '<':  operator.lt,
                 '==': operator.eq,
                 '!=': operator.ne,
                 '>=': operator.ge,
                 '<=': operator.le}

    POLARS_OPERATORS = {'+':  'add',
                        '-':  'sub',
                        '*':  'mul',
                        '/':  'truediv',
                        '//': 'floordiv',
                        '%':  'mod',
                        '**': 'pow',
                        '^':  'xor',
                        '&':  'and_',
                        '|':  'or_',

                        '>':  'gt',
                        '<':  'lt',
                        '==': 'eq',
                        '!=': 'ne',
                        '>=': 'ge',
                        '<=': 'le'}

    def __init__(self, vars: dict):
        """"""
        super().__init__()

        self.vars = {'DataFrame':     polars.DataFrame,
                     'LazyFrame':     polars.LazyFrame,
                     'Schema':        polars.Schema,
                     'Series':        polars.Series,
                     'SQLContext':    polars.SQLContext,

                     'Column':        polars.col,
                     'SQL':           polars.sql,
                     'SQLExpression': polars.sql_expr,

                     'DateTime':      datetime,
                     'Date':          date,
                     'Time':          time,

                     'Type':          _PolarsType,
                     'Source':        _PolarsSource,
                     'Selector':      _PolarsSelector,
                     'Utility':       _PolarsUtility}

        self.vars.update(self._prefix_vars(vars))

    def _prefix_vars(self, vars):
        """"""
        if isinstance(vars, dict):
            return {self._format_key(k): self._prefix_vars(v) for k, v in vars.items()}
        return vars

    def _format_key(self, key):
        """"""
        return f'$"{key}"' if ' ' in key else f'${key}'

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
            if isinstance(left, polars.Expr):
                op = self.POLARS_OPERATORS[op_str]
                left = getattr(left, op)(right)
                continue
            if isinstance(right, polars.Expr):
                op = self.POLARS_OPERATORS[op_str]
                if not isinstance(left, polars.Expr):
                    left = polars.lit(left)
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
            if isinstance(value, polars.Expr):
                return value.neg()
            return operator.neg(value)
        if op == 'not':
            return operator.not_(value)
        return value

    def atom(self, *args):
        """"""
        obj = args[0]
        if isinstance(obj, Token):
            obj = self.vars.get(obj.value)
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
                if arg.startswith('_'):
                    return obj # TODO: show errors to user
                if not hasattr(obj, arg):
                    return obj # TODO: show errors to user
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

    def pair_arg(self, *args):
        """"""
        return args

    def VAR(self, value: str):
        """"""
        value = value.removeprefix('$')
        value = value.strip("\"'")
        return self.vars.get(
            f'$"{value}"',
            self.vars.get(
                f"$'{value}'",
                self.vars.get(f'${value}')
            )
        )

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
            return json.loads(value)
        else:
            return value[1:-1].replace(r"\'", "'") \
                              .replace(r"\\", "\\")


parser = Lark(_GRAMMAR, parser = 'lalr')



def initialize() -> None:
    """"""
    pass
