# test_split_by_digit_to_nondigit.py
#
# Copyright (c) 2025 Naufan Rusyda Faikar <hello@naruaika.me>
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

from witt_strutil import split_by_digit_to_nondigit
import polars

def test_split_by_digit_to_nondigit():
    df = polars.DataFrame({
        'input': [
            '123ABC',
            'A1B2C',
            'Version2Beta',
            '123',
            'ABC',
        ],
        'expected': [
            ['123', 'ABC'],
            ['A1', 'B2', 'C'],
            ['Version2', 'Beta'],
            ['123'],
            ['ABC'],
        ],
    })
    df = df.with_columns(output=split_by_digit_to_nondigit('input'))

    assert df['output'].to_list() == df['expected'].to_list()