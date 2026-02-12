# formula_evaluator.py
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
from datetime import datetime
from datetime import date
from datetime import time
from difflib import get_close_matches
from functools import reduce
from typing import Any
import ast
import operator
import polars
import polars.selectors

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


class Evaluator():

    OPERATORS = {ast.Add:      operator.add,
                 ast.Sub:      operator.sub,
                 ast.Mult:     operator.mul,
                 ast.Div:      operator.truediv,
                 ast.FloorDiv: operator.floordiv,
                 ast.Mod:      operator.mod,
                 ast.Pow:      operator.pow,
                 ast.BitXor:   operator.xor,
                 ast.BitAnd:   operator.and_,
                 ast.BitOr:    operator.or_,

                 ast.Gt:       operator.gt,
                 ast.Lt:       operator.lt,
                 ast.Eq:       operator.eq,
                 ast.NotEq:    operator.ne,
                 ast.GtE:      operator.ge,
                 ast.LtE:      operator.le,

                 ast.Invert:   operator.invert,
                 ast.USub:     operator.neg,
                 ast.Not:      operator.not_}

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

        self.vars.update(vars)

    def evaluate(self, formula: str):
        """"""
        tree = ast.parse(formula)
        result = None
        for node in tree.body:
            result = self._visit(node)
        return result

    def _visit(self, node):
        """"""
        if isinstance(node, ast.UnaryOp):
            op = self.OPERATORS[type(node.op)]
            operand = self._visit(node.operand)
            return op(operand)

        if isinstance(node, ast.List):
            return [self._visit(elt) for elt in node.elts]

        if isinstance(node, ast.Tuple):
            return tuple(self._visit(elt) for elt in node.elts)

        if isinstance(node, ast.Dict):
            keys = [self._visit(k) for k in node.keys]
            values = [self._visit(v) for v in node.values]
            return dict(zip(keys, values))

        if isinstance(node, ast.Expr):
            return self._visit(node.value)

        if isinstance(node, ast.Assign):
            target = node.targets[0].id
            value = self._visit(node.value)
            self.vars[target] = value
            return value

        if isinstance(node, ast.Name):
            if node.id in self.vars:
                return self.vars[node.id]
            raise NameError(f"Variable '{node.id}' is not defined.")

        if isinstance(node, ast.Constant):
            return node.value

        if isinstance(node, ast.Call):
            func = self._visit(node.func)
            args = [self._visit(a) for a in node.args]
            kwargs = {k.arg: self._visit(k.value) for k in node.keywords}
            return func(*args, **kwargs)

        if isinstance(node, ast.Attribute):
            obj = self._visit(node.value)
            return getattr(obj, node.attr)

        if isinstance(node, ast.BinOp):
            left = self._visit(node.left)
            right = self._visit(node.right)
            op = self.OPERATORS[type(node.op)]
            return op(left, right)

        if isinstance(node, ast.Compare):
            left = self._visit(node.left)
            curr = left
            result = None
            for op, comp in zip(node.ops, node.comparators):
                right = self._visit(comp)
                op = self.OPERATORS[type(op)]
                comparison = op(curr, right)
                if result is None:
                    result = comparison
                else:
                    result = result & comparison
                curr = right
            return result

        if isinstance(node, ast.BoolOp):
            values = [self._visit(v) for v in node.values]
            if isinstance(node.op, ast.And):
                return reduce(op.and_, values)
            elif isinstance(node.op, ast.Or):
                return reduce(op.or_, values)
            return values

        if isinstance(node, ast.Lambda):
            return self._create_lambda(node)

        raise TypeError(f"Syntax '{type(node).__name__}' is not allowed.")

    def _create_lambda(self, node):
        """"""
        names = [arg.arg for arg in node.args.args]

        def do_create(*values):
            """"""
            local_vars = dict(zip(names, values))

            old_vars = self.vars.copy()
            self.vars.update(local_vars)

            try:
                return self._visit(node.body)
            except:
                pass # TODO: show errors to user
            finally:
                self.vars = old_vars

        return do_create



def initialize() -> None:
    """"""
    pass
