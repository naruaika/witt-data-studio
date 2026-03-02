# test_split_by_uppercase_to_lowercase.py
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

from witt_strutil import split_by_uppercase_to_lowercase
import polars

def test_split_by_uppercase_to_lowercase():
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
            ['S', 'ymbianOS'],
            ['W', 'inCE'],
            ['webOS'],
            ['iP', 'hone'],
            ['JSON', 'file'],
            ['GO', 'bject'],
            ['P', 'ython'],
            ['S', 'ony E', 'ricsson'],
            ['B', 'lackB', 'erry OS'],
        ],
    })
    df = df.with_columns(output=split_by_uppercase_to_lowercase('input'))

    assert df['output'].to_list() == df['expected'].to_list()