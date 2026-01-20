# utils_file.py
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

TEXT_CHARS = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})


def isbinfile(file_path: str) -> bool:
    """"""
    from os.path import isfile
    if not isfile(file_path or ''):
        return False
    is_binary = False
    with open(file_path, 'rb') as file:
        bytes = file.read(1024)
        is_binary = bool(bytes.translate(None, TEXT_CHARS))
    return is_binary


def get_file_format(file_path: str) -> str:
    """"""
    if '.' in file_path:
        return file_path.split('.')[-1].lower()
    return None
