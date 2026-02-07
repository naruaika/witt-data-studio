# transform_layout.py
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

def get_layout(action_name: str) -> tuple[str, list]:
    """"""
    match action_name:

        case 'choose-columns':
            return (
                _('Choose Columns'),
                [
                    (
                        [
                            _('Columns'),
                            _('Select one or more columns to keep'),
                        ],
                        'list-check',
                        '$all-columns',
                    ),
                ],
            )

        case 'remove-columns':
            return (
                _('Remove Columns'),
                [
                    (
                        [
                            _('Columns'),
                            _('Select one or more columns to remove'),
                        ],
                        'list-check',
                        '$all-columns',
                    ),
                ],
            )

        case 'keep-top-k-rows':
            return (
                _('Keep Top K Rows'),
                [
                    (_('No. Rows'), 'spin', (1, None, 0)),
                    (
                        [
                            _('Based On'),
                            _('Select column(s) to determine the top rows'),
                        ],
                        'list-check',
                        '$all-columns',
                    ),
                ],
            )

        case 'keep-bottom-k-rows':
            return (
                _('Keep Bottom K Rows'),
                [
                    (_('No. Rows'), 'spin', (1, None, 0)),
                    (
                        [
                            _('Based On'),
                            _('Select column(s) to determine the bottom rows'),
                        ],
                        'list-check',
                        '$all-columns',
                    ),
                ],
            )

        case 'keep-first-k-rows':
            return (
                _('Keep First K Rows'),
                [
                    (_('No. Rows'), 'spin', (1, None, 0)),
                ],
            )

        case 'keep-last-k-rows':
            return (
                _('Keep Last K Rows'),
                [
                    (_('No. Rows'), 'spin', (1, None, 0)),
                ],
            )

        case 'keep-range-of-rows':
            return (
                _('Keep Range of Rows'),
                [
                    (_('From Row'), 'spin'),
                    (_('No. Rows'), 'spin', (1, None, 0)),
                ],
            )

        case 'keep-every-nth-rows':
            return (
                _('Keep Every nth Rows'),
                [
                    (_('Nth Row'), 'spin', (1, None, 0)),
                    (_('From Row'), 'spin'),
                ],
            )

        case 'keep-duplicate-rows':
            return (
                _('Keep Duplicate Rows'),
                [
                    (
                        [
                            _('Based On'),
                            _('Select column(s) to determine the duplicate rows'),
                        ],
                        'list-check',
                        '$all-columns',
                    ),
                ],
            )

        case 'remove-first-k-rows':
            return (
                _('Remove First K Rows'),
                [
                    (_('No. Rows'), 'spin', (1, None, 0)),
                ],
            )

        case 'remove-last-k-rows':
            return (
                _('Remove Last K Rows'),
                [
                    (_('No. Rows'), 'spin', (1, None, 0)),
                ],
            )

        case 'remove-range-of-rows':
            return (
                _('Remove Range of Rows'),
                [
                    (_('From Row'), 'spin'),
                    (_('No. Rows'), 'spin', (1, None, 0)),
                ],
            )

        case 'remove-duplicate-rows':
            return (
                _('Remove Duplicate Rows'),
                [
                    (
                        _('Rows to Keep'),
                        'combo',
                        {
                            'any':   _('Any'),
                            'none':  _('None'),
                            'first': _('First'),
                            'last':  _('Last'),
                        },
                    ),
                    (_('Maintain Order'), 'switch'),
                    (
                        [
                            _('Based On'),
                            _('Select column(s) to determine the duplicate rows'),
                        ],
                        'list-check',
                        '$all-columns',
                    ),
                ],
            )

        case 'sort-rows':
            return (
                _('Sort Rows'),
                [
                    (
                        _('Level'),
                        'list-item',
                        [
                            ('dropdown', '$all-columns'),
                            (
                                'dropdown',
                                {
                                    'ascending':  _('Ascending'),
                                    'descending': _('Descending'),
                                },
                            ),
                        ],
                    ),
                ],
            )

        case 'transpose-table':
            return (
                _('Transpose Table'),
                [
                    (_('Include Header'), 'switch'),
                ],
            )

        case 'reverse-rows':
            return (_('Reverse Rows'), [])

        case 'change-data-type':
            return (
                _('Change Data Type'),
                [
                    (
                        _('Mapping'),
                        'list-item',
                        [
                            ('dropdown', '$all-columns'),
                            (
                                'dropdown',
                                {
                                    'date':        _('Date'),
                                    'time':        _('Time'),
                                    'datetime':    _('Datetime'),
                                    'duration':    _('Duration'),
                                    'text':        _('Text'),
                                    'boolean':     _('Boolean'),
                                    'categorical': _('Categorical'),
                                    'float32':     _('Float (32-Bit)'),
                                    'float64':     _('Float (64-Bit)'),
                                    'int8':        _('Integer (8-Bit)'),
                                    'int16':       _('Integer (16-Bit)'),
                                    'int32':       _('Integer (32-Bit)'),
                                    'int64':       _('Integer (64-Bit)'),
                                    'uint8':       _('Unsigned (8-Bit)'),
                                    'uint16':      _('Unsigned (16-Bit)'),
                                    'uint32':      _('Unsigned (32-Bit)'),
                                    'uint64':      _('Unsigned (64-Bit)'),
                                },
                            ),
                        ],
                    ),
                ],
            )

        case 'rename-columns':
            return (
                _('Rename Columns'),
                [
                    (
                        _('Mapping'),
                        'list-item',
                        [
                            ('dropdown', '$all-columns'),
                            ('entry'),
                        ],
                    ),
                ],
            )

        case 'replace-values':
            return (
                _('Replace Values'),
                [
                    (_('Search'), 'entry'),
                    (_('Replace'), 'entry'),
                    (
                        [
                            _('Search Options'),
                            _('The options below apply only to text columns. '
                              'Exact match always applies to non-text columns.'),
                        ],
                        'list-check:indexed',
                        [
                            _('Exact Match'),
                            _('Case Sensitive'),
                            _('Regular Exp.'),
                        ],
                    ),
                    (
                        [
                            _('Search On'),
                            _('Select column(s) to search for the value of. '
                              'Leave blank to search all columns.'),
                        ],
                        'list-check',
                        '$all-columns',
                    ),
                ],
            )

        case 'fill-blank-cells':
            return (
                _('Fill Blank Cells'),
                [
                    (
                        _('Strategy'),
                        'combo',
                        {
                            'forward':  _('Forward'),
                            'backward': _('Backward'),
                            'min':      _('Minimum'),
                            'max':      _('Maximum'),
                            'mean':     _('Mean'),
                            'zero':     _('Zero'),
                            'one':      _('One'),
                        },
                    ),
                    (
                        [
                            _('Columns'),
                            _('Select column(s) with blank cell(s) to fill. '
                              'Leave blank to fill all columns.'),
                        ],
                        'list-check',
                        '$all-columns',
                    ),
                ],
            )

        case 'split-column-by-delimiter':
            return (
                _('Split Column by Delimiter'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$string-columns:use-column',
                    ),
                    (
                        _('Delimiter'),
                        'combo:custom',
                        {
                            ',':  _('Comma'),
                            '=':  _('Equal Sign'),
                            ';':  _('Semicolon'),
                            ' ':  _('Space'),
                            '\t': _('Tab'),
                        },
                    ),
                    (
                        None,
                        'group',
                        [
                            (_('No. Columns'), 'spin', (1, None, 0)),
                            (
                                _('At Delimiter'),
                                'combo',
                                {
                                    'every': _('Every Occurrence'),
                                    'first': _('First Occurrence'),
                                },
                            ),
                        ],
                    ),
                ],
            )

        case 'split-column-by-number-of-characters':
            return (
                _('Split Column by Number of Characters'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$string-columns:use-column',
                    ),
                    (_('No. Characters'), 'spin', (1, None, 0)),
                    (
                        _('Strategy'),
                        'combo',
                        {
                            'first':  _('First'),
                            'last':   _('Last'),
                            'repeat': _('Repeat'),
                        },
                    ),
                ],
            )

        case 'split-column-by-positions':
            return (
                _('Split Column by Positions'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$string-columns:use-column',
                    ),
                    (_('Positions'), 'entry', '0, 1'),
                ],
            )

        case 'split-column-by-lowercase-to-uppercase':
            return (
                _('Split Column by Lowercase to Uppercase'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$string-columns:use-column',
                    ),
                ],
            )

        case 'split-column-by-uppercase-to-lowercase':
            return (
                _('Split Column by Uppercase to Lowercase'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$string-columns:use-column',
                    ),
                ],
            )

        case 'split-column-by-digit-to-nondigit':
            return (
                _('Split Column by Digit to Non-Digit'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$string-columns:use-column',
                    ),
                ],
            )

        case 'split-column-by-nondigit-to-digit':
            return (
                _('Split Column by Non-Digit to Digit'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$string-columns:use-column',
                    ),
                ],
            )

        case 'change-case-to-lowercase':
            return (
                _('Change Case to Lowercase'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$string-columns:use-column',
                    ),
                ],
            )

        case 'change-case-to-uppercase':
            return (
                _('Change Case to Uppercase'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$string-columns:use-column',
                    ),
                ],
            )

        case 'change-case-to-titlecase':
            return (
                _('Change Case to Title Case'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$string-columns:use-column',
                    ),
                ],
            )

        case 'trim-contents':
            return (
                _('Trim Contents'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$string-columns:use-column',
                    ),
                    (
                        _('Characters'),
                        'combo:custom',
                        {
                            ' \n': _('Spaces & Newlines'),
                            ' ':   _('Spaces Only'),
                            '\n':  _('Newlines Only'),
                        },
                    ),
                ],
            )

        case 'clean-contents':
            return (
                _('Clean Contents'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$string-columns:use-column',
                    ),
                    (
                        [
                            _('To Keep'),
                            _('Select one or more control characters to keep'),
                        ],
                        'list-check:indexed',
                        [
                            _('Newlines'),
                            _('Tabs'),
                        ],
                    ),
                ],
            )

        case 'add-prefix':
            return (
                _('Add Prefix'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$string-columns:use-column',
                    ),
                    (_('Prefix'), 'entry'),
                ],
            )

        case 'add-suffix':
            return (
                _('Add Suffix'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$string-columns:use-column',
                    ),
                    (_('Suffix'), 'entry'),
                ],
            )

        case 'merge-columns':
            return (
                _('Merge Columns'),
                [
                    (
                        [
                            _('Columns'),
                            _('Select two or more columns to merge'),
                        ],
                        'list-check',
                        '$all-columns:use-column',
                    ),
                    (
                        _('Separator'),
                        'combo:custom',
                        {
                            '':   _('None'),
                            ':':  _('Colon'),
                            ',':  _('Comma'),
                            '=':  _('Equal Sign'),
                            ';':  _('Semicolon'),
                            ' ':  _('Space'),
                            '\t': _('Tab'),
                        },
                    ),
                    (_('Alias') + '?', 'entry'),
                ],
            )

        case 'extract-text-length':
            return (
                _('Extract Text Length'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$string-columns:use-column',
                    ),
                ],
            )

        case 'extract-first-characters':
            return (
                _('Extract First Characters'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$string-columns:use-column',
                    ),
                    (_('No. Characters'), 'spin', (1, None, 0)),
                ],
            )

        case 'extract-last-characters':
            return (
                _('Extract Last Characters'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$string-columns:use-column',
                    ),
                    (_('No. Characters'), 'spin', (1, None, 0)),
                ],
            )

        case 'extract-text-in-range':
            return (
                _('Extract Text in Range'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$string-columns:use-column',
                    ),
                    (_('Starting Index'), 'spin', (0, None, 0)),
                    (_('No. Characters'), 'spin', (1, None, 0)),
                ],
            )

        case 'extract-text-before-delimiter':
            return (
                _('Extract Text Before Delimiter'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$string-columns:use-column',
                    ),
                    (_('Delimiter'), 'entry'),
                ],
            )

        case 'extract-text-after-delimiter':
            return (
                _('Extract Text After Delimiter'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$string-columns:use-column',
                    ),
                    (_('Delimiter'), 'entry'),
                ],
            )

        case 'extract-text-between-delimiters':
            return (
                _('Extract Text Between Delimiters'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$string-columns:use-column',
                    ),
                    (_('Start Delimiter'), 'entry'),
                    (_('End Delimiter'), 'entry'),
                ],
            )

        case 'calculate-minimum':
            return (
                _('Calculate Minimum'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                ],
            )

        case 'calculate-maximum':
            return (
                _('Calculate Maximum'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                ],
            )

        case 'calculate-summation':
            return (
                _('Calculate Summation'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                ],
            )

        case 'calculate-median':
            return (
                _('Calculate Median'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                ],
            )

        case 'calculate-average':
            return (
                _('Calculate Average'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                ],
            )

        case 'calculate-standard-deviation':
            return (
                _('Calculate Standard Deviation'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                ],
            )

        case 'count-values':
            return (
                _('Count Values'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$all-columns:use-column',
                    ),
                ],
            )

        case 'count-distinct-values':
            return (
                _('Count Distinct Values'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$all-columns:use-column',
                    ),
                ],
            )

        case 'calculate-addition':
            return (
                _('Calculate Addition'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                    (_('Value'), 'entry', 0.0),
                ],
            )

        case 'calculate-multiplication':
            return (
                _('Calculate Multiplication'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                    (_('Value'), 'entry', 0.0),
                ],
            )

        case 'calculate-subtraction':
            return (
                _('Calculate Subtraction'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                    (_('Value'), 'entry', 0.0),
                ],
            )

        case 'calculate-division':
            return (
                _('Calculate Division'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                    (_('Value'), 'entry', 0.0),
                ],
            )

        case 'calculate-integer-division':
            return (
                _('Calculate Integer-Division'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                    (_('Value'), 'entry', 0.0),
                ],
            )

        case 'calculate-modulo':
            return (
                _('Calculate Modulo'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                    (_('Value'), 'entry', 0.0),
                ],
            )

        case 'calculate-percentage':
            return (
                _('Calculate Percentage'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                    (_('Value'), 'entry', 0.0),
                ],
            )

        case 'calculate-percent-of':
            return (
                _('Calculate Percent Of'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                    (_('Value'), 'entry', 0.0),
                ],
            )

        case 'calculate-absolute':
            return (
                _('Calculate Absolute'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                ],
            )

        case 'calculate-square-root':
            return (
                _('Calculate Square Root'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                ],
            )

        case 'calculate-square':
            return (
                _('Calculate Square'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                ],
            )

        case 'calculate-cube':
            return (
                _('Calculate Cube'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                ],
            )

        case 'calculate-power-k':
            return (
                _('Calculate Power K'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                    (_('Value'), 'entry', 1.0),
                ],
            )

        case 'calculate-exponent':
            return (
                _('Calculate Exponent'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                ],
            )

        case 'calculate-base-10':
            return (
                _('Calculate Base-10'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                ],
            )

        case 'calculate-natural':
            return (
                _('Calculate Natural'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                ],
            )

        case 'calculate-sine':
            return (
                _('Calculate Sine'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                ],
            )

        case 'calculate-cosine':
            return (
                _('Calculate Cosine'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                ],
            )

        case 'calculate-tangent':
            return (
                _('Calculate Tangent'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                ],
            )

        case 'calculate-arcsine':
            return (
                _('Calculate Arcsine'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                ],
            )

        case 'calculate-arccosine':
            return (
                _('Calculate Arccosine'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                ],
            )

        case 'calculate-arctangent':
            return (
                _('Calculate Arctangent'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                ],
            )

        case 'round-value':
            return (
                _('Round Value'),
                [
                    (
                        _('Column'),
                        'combo',
                        '$numeric-columns:use-column',
                    ),
                    (_('Decimals'), 'spin', (0, None, 0)),
                    (
                        _('Mode'),
                        'combo',
                        {
                            'bankers':    _('Banker\'s'),
                            'commercial': _('Commercial'),
                        },
                    ),
                ],
            )

    raise KeyError()
