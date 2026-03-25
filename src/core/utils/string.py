# string.py
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

from string import digits

def unique_name(default_name: str,
                list_names:   list[str],
                new_name:     str = '',
                old_name:     str = '',
                separator:    str = '',
                ) ->          str:
    """"""
    def do_generate(in_name: str) -> str:
        """"""
        import re
        suffix = 1
        pattern = rf'{in_name}{separator}(\d+)'
        for ex_name in list_names:
            if match := re.match(pattern, ex_name):
                suffix = max(suffix, int(match.group(1)) + 1)
        return f'{in_name}{separator}{suffix}'

    # Remove all trailing digits if any
    default_name = default_name.rstrip(digits)

    if not new_name:
        return do_generate(default_name)

    # Remove characters `@$!:` to prevent from
    # possible collision with internal naming.
    new_name = new_name.strip().strip('@$!:')

    # Generate a new column name if needed only
    if new_name != old_name and \
            new_name in list_names:
        return do_generate(new_name)

    return new_name
