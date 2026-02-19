# date_picker.py
#
# Copyright 2025 Naufan Rusyda Faikar
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

from gi.repository import Gdk
from gi.repository import Gtk

class DatePicker(Gtk.Calendar):

    __gtype_name__ = 'DatePicker'

    def __init__(self,
                 *args:    list,
                 **kwargs: dict,
                 ) ->      None:
        """"""
        super().__init__(*args, **kwargs)

        header = self.get_first_child()
        grid = header.get_next_sibling()

        day_name = grid.get_first_child()
        day_name.set_label('S')

        day_name = day_name.get_next_sibling()
        day_name.set_label('M')

        day_name = day_name.get_next_sibling()
        day_name.set_label('T')

        day_name = day_name.get_next_sibling()
        day_name.set_label('W')

        day_name = day_name.get_next_sibling()
        day_name.set_label('T')

        day_name = day_name.get_next_sibling()
        day_name.set_label('F')

        day_name = day_name.get_next_sibling()
        day_name.set_label('S')
