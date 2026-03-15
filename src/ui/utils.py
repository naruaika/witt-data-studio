# utils.py
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

from gi.repository import Adw

def get_accent_color() -> str:
    """"""
    style_manager = Adw.StyleManager.get_default()

    accent_color = style_manager.get_accent_color_rgba()

    r = int(accent_color.red   * 255)
    g = int(accent_color.green * 255)
    b = int(accent_color.blue  * 255)

    hex_color = f'#{r:02x}{g:02x}{b:02x}'

    return hex_color


def get_standalone_accent_color() -> str:
    """"""
    style_manager = Adw.StyleManager.get_default()

    prefers_dark = style_manager.get_dark()
    accent_color = style_manager.get_accent_color()
    accent_color = accent_color.to_standalone_rgba(prefers_dark)

    r = int(accent_color.red   * 255)
    g = int(accent_color.green * 255)
    b = int(accent_color.blue  * 255)

    hex_color = f'#{r:02x}{g:02x}{b:02x}'

    return hex_color


def get_prefers_dark() -> bool:
    """"""
    style_manager = Adw.StyleManager.get_default()
    prefers_dark = style_manager.get_dark()
    return prefers_dark
