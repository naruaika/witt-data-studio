# __init__.py
#
# Copyright 2025 Naufan Rusyda Faikar <hello@naruaika.me>
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

from .boolean import *
from .decimal import *
from .integer import *
from .string import *

from .read_file import *
from .read_database import *

from .sheet import *
from .viewer import *

from .custom_formula import *

from .choose_columns import *
from .remove_columns import *

from .keep_top_k_rows import *
from .keep_bottom_k_rows import *
from .keep_first_k_rows import *
from .keep_last_k_rows import *
from .keep_range_of_rows import *
from .keep_every_nth_rows import *
from .keep_duplicate_rows import *

from .remove_first_k_rows import *
from .remove_last_k_rows import *
from .remove_range_of_rows import *
from .remove_duplicate_rows import *

from .sort_rows import *
from .filter_rows import *

from .join_tables import *
from .group_by import *
from .transpose_table import *
from .reverse_rows import *

from .change_data_type import *
from .rename_columns import *
from .replace_values import *
from .fill_blank_values import *

from .split_column_by_delimiter import *
from .split_column_by_number_of_characters import *
from .split_column_by_positions import *

from .split_column_by_lowercase_to_uppercase import *
from .split_column_by_uppercase_to_lowercase import *
from .split_column_by_digit_to_non_digit import *
from .split_column_by_non_digit_to_digit import *

from .change_case_to_lowercase import *
from .change_case_to_uppercase import *
from .change_case_to_titlecase import *

from .trim_contents import *
from .clean_contents import *

from .add_prefix import *
from .add_suffix import *

from .merge_columns import *

from .extract_text_length import *
from .extract_first_characters import *
from .extract_last_characters import *
from .extract_text_in_range import *
from .extract_text_before_delimiter import *
from .extract_text_after_delimiter import *
from .extract_text_between_delimiters import *

from .calculate_minimum import *
from .calculate_maximum import *
from .calculate_summation import *
from .calculate_median import *
from .calculate_average import *
from .calculate_standard_deviation import *
from .count_values import *
from .count_distinct_values import *

from .calculate_addition import *
from .calculate_multiplication import *
from .calculate_subtraction import *
from .calculate_division import *
from .calculate_integer_division import *
from .calculate_modulo import *
from .calculate_percentage import *
from .calculate_percent_of import *

from .calculate_absolute import *
from .calculate_square_root import *
from .calculate_square import *
from .calculate_cube import *
from .calculate_power_k import *
from .calculate_exponent import *
from .calculate_base_10 import *
from .calculate_natural import *

from .calculate_sine import *
from .calculate_cosine import *
from .calculate_tangent import *
from .calculate_arcsine import *
from .calculate_arccosine import *
from .calculate_arctangent import *

from .round_value import *

from .calculate_is_even import *
from .calculate_is_odd import *
from .extract_value_sign import *

_registered_nodes = [

    NodeBoolean(),
    NodeDecimal(),
    NodeInteger(),
    NodeString(),

    NodeReadFile(),
    NodeReadDatabase(),

    NodeSheet(),
    NodeViewer(),

    NodeCustomFormula(),

    NodeChooseColumns(),
    NodeRemoveColumns(),

    NodeKeepTopKRows(),
    NodeKeepBottomKRows(),
    NodeKeepFirstKRows(),
    NodeKeepLastKRows(),
    NodeKeepRangeOfRows(),
    NodeKeepEveryNthRows(),
    NodeKeepDuplicateRows(),

    NodeRemoveFirstKRows(),
    NodeRemoveLastKRows(),
    NodeRemoveRangeOfRows(),
    NodeRemoveDuplicateRows(),

    NodeSortRows(),
    NodeFilterRows(),

    NodeJoinTables(),
    NodeGroupBy(),
    NodeTransposeTable(),
    NodeReverseRows(),

    NodeChangeDataType(),
    NodeRenameColumns(),
    NodeReplaceValues(),
    NodeFillBlankValues(),

    NodeSplitColumnByDelimiter(),
    NodeSplitColumnByNumberOfCharacters(),
    NodeSplitColumnByPositions(),

    NodeSplitColumnByLowercaseToUppercase(),
    NodeSplitColumnByUppercaseToLowercase(),
    NodeSplitColumnByDigitToNonDigit(),
    NodeSplitColumnByNonDigitToDigit(),

    NodeChangeCaseToLowercase(),
    NodeChangeCaseToUppercase(),
    NodeChangeCaseToTitleCase(),

    NodeTrimContents(),
    NodeCleanContents(),

    NodeAddPrefix(),
    NodeAddSuffix(),

    NodeMergeColumns(),

    NodeExtractTextLength(),
    NodeExtractFirstCharacters(),
    NodeExtractLastCharacters(),
    NodeExtractTextInRange(),
    NodeExtractTextBeforeDelimiter(),
    NodeExtractTextAfterDelimiter(),
    NodeExtractTextBetweenDelimiters(),

    NodeCalculateMinimum(),
    NodeCalculateMaximum(),
    NodeCalculateSummation(),
    NodeCalculateMedian(),
    NodeCalculateAverage(),
    NodeCalculateStandardDeviation(),
    NodeCountValues(),
    NodeCountDistinctValues(),

    NodeCalculateAddition(),
    NodeCalculateMultiplication(),
    NodeCalculateSubtraction(),
    NodeCalculateDivision(),
    NodeCalculateIntegerDivision(),
    NodeCalculateModulo(),
    NodeCalculatePercentage(),
    NodeCalculatePercentOf(),

    NodeCalculateAbsolute(),
    NodeCalculateSquareRoot(),
    NodeCalculateSquare(),
    NodeCalculateCube(),
    NodeCalculatePowerK(),
    NodeCalculateExponent(),
    NodeCalculateBase10(),
    NodeCalculateNatural(),

    NodeCalculateSine(),
    NodeCalculateCosine(),
    NodeCalculateTangent(),
    NodeCalculateArcsine(),
    NodeCalculateArccosine(),
    NodeCalculateArctangent(),

    NodeRoundValue(),

    NodeCalculateIsEven(),
    NodeCalculateIsOdd(),
    NodeExtractValueSign(),
]


def create_new_node(name: str,
                    x:    int,
                    y:    int,
                    ) ->  NodeFrame:
    """"""
    for node in _registered_nodes:
        if name in {node.ndname, node.action}:
            return node.new(x, y)
    return NodeFrame(name, x, y)
