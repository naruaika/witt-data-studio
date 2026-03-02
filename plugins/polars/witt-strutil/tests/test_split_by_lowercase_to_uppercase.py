# test_split_by_lowercase_to_uppercase.py
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

from witt_strutil import split_by_lowercase_to_uppercase
import polars

def test_split_by_lowercase_to_uppercase():
    df = polars.DataFrame({
        'input': [
            'SymbianOS',
            'WinCE',
            'webOS',
            'iPhone',
            'JSONfile',
            'GObject',
            'Python',
            'Sony Ericsson',
            'BlackBerry OS',
        ],
        'expected': [
            ['Symbian', 'OS'],
            ['Win', 'CE'],
            ['web', 'OS'],
            ['i', 'Phone'],
            ['JSONfile'],
            ['GObject'],
            ['Python'],
            ['Sony Ericsson'],
            ['Black', 'Berry OS'],
        ],
    })
    df = df.with_columns(output=split_by_lowercase_to_uppercase('input'))

    assert df['output'].to_list() == df['expected'].to_list()