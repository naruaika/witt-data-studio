# test_split_by_character_transition.py
#
# Copyright (c) 2025 Naufan Rusyda Faikar <hello@naruaika.me>
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