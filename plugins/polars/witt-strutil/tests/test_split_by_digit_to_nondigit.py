# test_split_by_digit_to_nondigit.py
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