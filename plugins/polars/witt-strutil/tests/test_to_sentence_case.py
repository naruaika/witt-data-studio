# test_to_sentence_case.py
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

from witt_strutil import to_sentence_case
import polars

def test_to_sentence_case():
    df = polars.DataFrame({
        'input': [
            'lorem. ipsum! dolor? sit amet.',
            'lorem.ipsum!dolor?sit amet.',
            'UPPERCASE',
            'lowercase',
            'kebab-case',
            'snake_case',
            'camelCase',
            'PascalCase',
            'CONSTANT_CASE',
            'dot.case',
            'Sentence case',
            None,
        ],
        'expected': [
            'Lorem. Ipsum! Dolor? Sit amet.',
            'Lorem.ipsum!dolor?sit amet.',
            'Uppercase',
            'Lowercase',
            'Kebab-case',
            'Snake_case',
            'Camel case',
            'Pascal case',
            'Constant_case',
            'Dot.case',
            'Sentence case',
            None,
        ],
    })
    df = df.with_columns(output=to_sentence_case('input'))

    assert df['output'].to_list() == df['expected'].to_list()