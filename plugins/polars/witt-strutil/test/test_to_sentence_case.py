# test_to_sentence_case.py
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