# test_split_by_uppercase_to_lowercase.py
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