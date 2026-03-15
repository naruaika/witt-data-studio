# test_pig_latinnify.py
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

from witt_strutil import pig_latinnify
import polars

def test_pig_latinnify():
    df = polars.DataFrame({
        'input': [
            'he does not know',
            'this',
            'is',
            'banana',
            'black',
            'smile',
            'straight',
            'hello!',
        ],
        'expected': [
            'ehay oesday otnay owknay',
            'isthay',
            'isway',
            'ananabay',
            'ackblay',
            'ilesmay',
            'aightstray',
            'ellohay!',
        ],
    })
    df = df.with_columns(output=pig_latinnify('input'))

    assert df['output'].to_list() == df['expected'].to_list()