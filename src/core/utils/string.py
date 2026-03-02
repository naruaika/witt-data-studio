# string.py
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
        for ex_name in list_names:
            if match := re.match(rf'{in_name}{separator}(\d+)', ex_name):
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
    if new_name != old_name and new_name in list_names:
        return do_generate(new_name)

    return new_name
