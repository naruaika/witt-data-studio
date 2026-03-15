# file.py
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
