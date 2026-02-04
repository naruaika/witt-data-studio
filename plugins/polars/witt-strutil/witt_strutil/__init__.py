from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from warnings import deprecated

from polars import Expr
from polars.plugins import register_plugin_function

from witt_strutil._internal import __version__ as __version__

if TYPE_CHECKING:
    from witt_strutil.typing import IntoExprColumn

LIB = Path(__file__).parent

def pig_latinnify(expression: IntoExprColumn) -> Expr:
    """"""
    return register_plugin_function(plugin_path    = LIB,
                                    function_name  = 'pig_latinnify',
                                    args           = [expression],
                                    is_elementwise = True)

def split_by_character_transition(expression: IntoExprColumn,
                                  before:     list[str],
                                  after:      list[str],
                                  ) ->        Expr:
    """"""
    return register_plugin_function(plugin_path    = LIB,
                                    function_name  = 'split_by_character_transition',
                                    args           = [expression],
                                    kwargs         = {'before': before, 'after': after},
                                    is_elementwise = True)

@deprecated('Use split_by_character_transition instead')
def split_by_lowercase_to_uppercase(expression: IntoExprColumn) -> Expr:
    """"""
    return register_plugin_function(plugin_path    = LIB,
                                    function_name  = 'split_by_lowercase_to_uppercase',
                                    args           = [expression],
                                    is_elementwise = True)

@deprecated('Use split_by_character_transition instead')
def split_by_uppercase_to_lowercase(expression: IntoExprColumn) -> Expr:
    """"""
    return register_plugin_function(plugin_path    = LIB,
                                    function_name  = 'split_by_uppercase_to_lowercase',
                                    args           = [expression],
                                    is_elementwise = True)

@deprecated('Use split_by_character_transition instead')
def split_by_digit_to_nondigit(expression: IntoExprColumn) -> Expr:
    """"""
    return register_plugin_function(plugin_path    = LIB,
                                    function_name  = 'split_by_digit_to_nondigit',
                                    args           = [expression],
                                    is_elementwise = True)

@deprecated('Use split_by_character_transition instead')
def split_by_nondigit_to_digit(expression: IntoExprColumn) -> Expr:
    """"""
    return register_plugin_function(plugin_path    = LIB,
                                    function_name  = 'split_by_nondigit_to_digit',
                                    args           = [expression],
                                    is_elementwise = True)

def to_sentence_case(expression: IntoExprColumn) -> Expr:
    """"""
    return register_plugin_function(plugin_path    = LIB,
                                    function_name  = 'to_sentence_case',
                                    args           = [expression],
                                    is_elementwise = True)

def to_sponge_case(expression: IntoExprColumn) -> Expr:
    """"""
    return register_plugin_function(plugin_path    = LIB,
                                    function_name  = 'to_sponge_case',
                                    args           = [expression],
                                    is_elementwise = True)