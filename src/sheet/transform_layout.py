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
                    (_('No. Rows'), 'spin'),
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
                    (_('No. Rows'), 'spin'),
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
                    (_('No. Rows'), 'spin'),
                ],
            )

        case 'keep-last-k-rows':
            return (
                _('Keep Last K Rows'),
                [
                    (_('No. Rows'), 'spin'),
                ],
            )

        case 'keep-range-of-rows':
            return (
                _('Keep Range of Rows'),
                [
                    (_('From Row'), 'spin'),
                    (_('No. Rows'), 'spin'),
                ],
            )

        case 'keep-every-nth-rows':
            return (
                _('Keep Every nth Rows'),
                [
                    (_('Nth Row'), 'spin'),
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
                    (_('No. Rows'), 'spin'),
                ],
            )

        case 'remove-last-k-rows':
            return (
                _('Remove Last K Rows'),
                [
                    (_('No. Rows'), 'spin'),
                ],
            )

        case 'remove-range-of-rows':
            return (
                _('Remove Range of Rows'),
                [
                    (_('From Row'), 'spin'),
                    (_('No. Rows'), 'spin'),
                ],
            )

        case 'remove-duplicate-rows':
            return (
                _('Remove Duplicate Rows'),
                [
                    (
                        _('Rows to Keep'),
                        'combo',
                        [
                            _('Any'),
                            _('None'),
                            _('First'),
                            _('Last'),
                        ],
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
                                [
                                    _('Ascending'),
                                    _('Descending'),
                                ],
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

        case 'convert-data-type':
            return (
                _('Convert Data Type'),
                [
                    (
                        _('Mapping'),
                        'list-item',
                        [
                            ('dropdown', '$all-columns'),
                            (
                                'dropdown',
                                [
                                    _('Date'),
                                    _('Time'),
                                    _('Datetime'),
                                    _('Duration'),
                                    _('Text'),
                                    _('Boolean'),
                                    _('Categorical'),
                                    _('Decimal'),
                                    _('Float (32-Bit)'),
                                    _('Float (64-Bit)'),
                                    _('Integer (8-Bit)'),
                                    _('Integer (16-Bit)'),
                                    _('Integer (32-Bit)'),
                                    _('Integer (64-Bit)'),
                                    _('Unsigned (8-Bit)'),
                                    _('Unsigned (16-Bit)'),
                                    _('Unsigned (32-Bit)'),
                                    _('Unsigned (64-Bit)'),
                                ],
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

    raise KeyError()
