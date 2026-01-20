# utils.py
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

from gi.repository import Adw

def get_accent_color() -> str:
    """"""
    style_manager = Adw.StyleManager.get_default()
    accent_color = style_manager.get_accent_color_rgba()

    r = int(accent_color.red * 255)
    g = int(accent_color.green * 255)
    b = int(accent_color.blue * 255)

    hex_color = f'#{r:02x}{g:02x}{b:02x}'

    return hex_color


def get_standalone_accent_color() -> str:
    """"""
    style_manager = Adw.StyleManager.get_default()
    prefers_dark = style_manager.get_dark()
    accent_color = style_manager.get_accent_color()
    accent_color = accent_color.to_standalone_rgba(prefers_dark)

    r = int(accent_color.red * 255)
    g = int(accent_color.green * 255)
    b = int(accent_color.blue * 255)

    hex_color = f'#{r:02x}{g:02x}{b:02x}'

    return hex_color


def get_prefers_dark() -> bool:
    """"""
    style_manager = Adw.StyleManager.get_default()
    prefers_dark = style_manager.get_dark()
    return prefers_dark
