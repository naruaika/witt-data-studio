# __init__.py
#
# Copyright 2025 Naufan Rusyda Faikar <hello@naruaika.me>
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

from .boolean import *
from .decimal import *
from .integer import *
from .string  import *

from .read_file     import *
from .read_database import *

from .sheet  import *
from .viewer import *

from .custom_formula import *

from .choose_columns import *
from .remove_columns import *

from .keep_top_k_rows     import *
from .keep_bottom_k_rows  import *
from .keep_first_k_rows   import *
from .keep_last_k_rows    import *
from .keep_range_of_rows  import *
from .keep_every_nth_rows import *
from .keep_duplicate_rows import *

from .remove_first_k_rows   import *
from .remove_last_k_rows    import *
from .remove_range_of_rows  import *
from .remove_duplicate_rows import *

from .sort_rows   import *
from .filter_rows import *

from .merge_tables import *

from .duplicate_column import *

from .group_by        import *
from .transpose_table import *
from .reverse_rows    import *

from .change_data_type  import *
from .rename_columns    import *
from .replace_values    import *
from .fill_blank_values import *

from .split_column_by_delimiter            import *
from .split_column_by_number_of_characters import *
from .split_column_by_positions            import *

from .split_column_by_lowercase_to_uppercase import *
from .split_column_by_uppercase_to_lowercase import *
from .split_column_by_digit_to_non_digit     import *
from .split_column_by_non_digit_to_digit     import *

from .change_case_to_lowercase import *
from .change_case_to_uppercase import *
from .change_case_to_titlecase import *

from .trim_contents  import *
from .clean_contents import *

from .add_prefix import *
from .add_suffix import *

from .merge_columns import *

from .extract_text_length             import *
from .extract_first_characters        import *
from .extract_last_characters         import *
from .extract_text_in_range           import *
from .extract_text_before_delimiter   import *
from .extract_text_after_delimiter    import *
from .extract_text_between_delimiters import *

from .calculate_minimum            import *
from .calculate_maximum            import *
from .calculate_summation          import *
from .calculate_median             import *
from .calculate_average            import *
from .calculate_standard_deviation import *
from .count_values                 import *
from .count_distinct_values        import *

from .calculate_addition         import *
from .calculate_multiplication   import *
from .calculate_subtraction      import *
from .calculate_division         import *
from .calculate_integer_division import *
from .calculate_modulo           import *
from .calculate_percentage       import *
from .calculate_percent_of       import *

from .calculate_absolute    import *
from .calculate_square_root import *
from .calculate_square      import *
from .calculate_cube        import *
from .calculate_power_k     import *
from .calculate_exponent    import *
from .calculate_base_10     import *
from .calculate_natural     import *

from .calculate_sine       import *
from .calculate_cosine     import *
from .calculate_tangent    import *
from .calculate_arcsine    import *
from .calculate_arccosine  import *
from .calculate_arctangent import *

from .round_value import *

from .calculate_is_even  import *
from .calculate_is_odd   import *
from .extract_value_sign import *

from .extract_age              import *
from .extract_date_only        import *
from .extract_year             import *
from .extract_start_of_year    import *
from .extract_end_of_year      import *
from .extract_month            import *
from .extract_start_of_month   import *
from .extract_end_of_month     import *
from .extract_days_in_month    import *
from .extract_name_of_month    import *
from .extract_quarter_of_year  import *
from .extract_start_of_quarter import *
from .extract_end_of_quarter   import *
from .extract_week_of_year     import *
from .extract_week_of_month    import *
from .extract_start_of_week    import *
from .extract_end_of_week      import *
from .extract_day              import *
from .extract_day_of_week      import *
from .extract_day_of_year      import *
from .extract_start_of_day     import *
from .extract_end_of_day       import *
from .extract_name_of_day      import *

from .extract_time_only import *
from .extract_hour      import *
from .extract_minute    import *
from .extract_second    import *

from .calculate_earliest import *
from .calculate_latest   import *

from .extract_days          import *
from .extract_hours         import *
from .extract_minutes       import *
from .extract_seconds       import *
from .extract_total_years   import *
from .extract_total_days    import *
from .extract_total_hours   import *
from .extract_total_minutes import *
from .extract_total_seconds import *

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

    NodeMergeTables(),

    NodeDuplicateColumn(),

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

    NodeExtractAge(),
    NodeExtractDateOnly(),
    NodeExtractYear(),
    NodeExtractStartOfYear(),
    NodeExtractEndOfYear(),
    NodeExtractMonth(),
    NodeExtractStartOfMonth(),
    NodeExtractEndOfMonth(),
    NodeExtractDaysInMonth(),
    NodeExtractNameOfMonth(),
    NodeExtractQuarterOfYear(),
    NodeExtractStartOfQuarter(),
    NodeExtractEndOfQuarter(),
    NodeExtractWeekOfYear(),
    NodeExtractWeekOfMonth(),
    NodeExtractStartOfWeek(),
    NodeExtractEndOfWeek(),
    NodeExtractDay(),
    NodeExtractDayOfWeek(),
    NodeExtractDayOfYear(),
    NodeExtractStartOfDay(),
    NodeExtractEndOfDay(),
    NodeExtractNameOfDay(),

    NodeExtractTimeOnly(),
    NodeExtractHour(),
    NodeExtractMinute(),
    NodeExtractSecond(),

    NodeCalculateEarliest(),
    NodeCalculateLatest(),

    NodeExtractDays(),
    NodeExtractHours(),
    NodeExtractMinutes(),
    NodeExtractSeconds(),
    NodeExtractTotalYears(),
    NodeExtractTotalDays(),
    NodeExtractTotalHours(),
    NodeExtractTotalMinutes(),
    NodeExtractTotalSeconds(),
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
