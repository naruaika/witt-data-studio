# test_split_by_nondigit_to_digit.py
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

from witt_strutil import split_by_nondigit_to_digit
import polars

def test_split_by_nondigit_to_digit():
    df = polars.DataFrame({
        'input': [
            'ABC123',
            'A1B2C',
            'Version2Beta',
            '123',
            'ABC',
        ],
        'expected': [
            ['ABC', '123'],
            ['A', '1B', '2C'],
            ['Version', '2Beta'],
            ['123'],
            ['ABC'],
        ],
    })
    df = df.with_columns(output=split_by_nondigit_to_digit('input'))

    assert df['output'].to_list() == df['expected'].to_list()