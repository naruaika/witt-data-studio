# test_split_by_character_transition.py
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

from witt_strutil import split_by_character_transition
import polars
import string

def test_split_by_character_transition():
    # Lowercase to Uppercase
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
    before = list(string.ascii_lowercase)
    after  = list(string.ascii_uppercase)
    df = df.with_columns(output=split_by_character_transition('input', before, after))
    assert df['output'].to_list() == df['expected'].to_list()

    # Uppercase to Lowercase
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
    before = list(string.ascii_uppercase)
    after  = list(string.ascii_lowercase)
    df = df.with_columns(output=split_by_character_transition('input', before, after))
    assert df['output'].to_list() == df['expected'].to_list()

    # Digit to Non-Digit
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
    before = list(string.digits)
    after  = list(string.ascii_letters)
    df = df.with_columns(output=split_by_character_transition('input', before, after))
    assert df['output'].to_list() == df['expected'].to_list()

    # Non-Digit to Digit
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
    before = list(string.ascii_letters)
    after  = list(string.digits)
    df = df.with_columns(output=split_by_character_transition('input', before, after))
    assert df['output'].to_list() == df['expected'].to_list()