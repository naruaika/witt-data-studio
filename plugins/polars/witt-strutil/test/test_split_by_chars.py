# test_split_by_chars.py
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

from witt_strutil import split_by_chars
import polars

def test_split_by_chars():
    input = polars.DataFrame({
        'input': [
            'Nadya Arina, Refal Hady, Giorgino Abraham, Anggika Bolsterli, Laura Theux, Christine Hakim',
            'Maudy Koesnaedi, Rano Karno, Cornelia Agatha, Mandra Naih, Aminah Tjendrakasih, Suty Karno',
            'Shay Mitchell; Liza Soberano; Jon Jon Briones; Darren Criss; Manny Jacinto; Dante Basco',
        ],
    })

    output = polars.select(split_by_chars(input.get_column('input'), characters=',;')).to_series().to_list()

    expected = [
        'Nadya Arina', 'Refal Hady', 'Giorgino Abraham', 'Anggika Bolsterli', 'Laura Theux', 'Christine Hakim',
        'Maudy Koesnaedi', 'Rano Karno', 'Cornelia Agatha', 'Mandra Naih', 'Aminah Tjendrakasih', 'Suty Karno',
        'Shay Mitchell', 'Liza Soberano', 'Jon Jon Briones', 'Darren Criss', 'Manny Jacinto', 'Dante Basco',
    ]

    assert output == expected