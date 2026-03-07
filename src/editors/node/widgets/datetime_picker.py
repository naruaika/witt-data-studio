# datetime_picker.py
#
# Copyright 2025 Naufan Rusyda Faikar <hello@naruaika.me>
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

from gi.repository import Gtk
import datetime

from .date_picker import *
from .time_picker import *

class NodeDateTimePicker(Gtk.Box):

    __gtype_name__ = 'NodeDateTimePicker'

    def __init__(self,
                 get_data: callable,
                 set_data: callable,
                 ) ->      None:
        """"""
        default: datetime.datetime = get_data()

        super().__init__(orientation = Gtk.Orientation.VERTICAL,
                         hexpand     = True)
        self.add_css_class('linked')

        current_date = default.date()
        current_time = default.time()

        def update_datetime() -> None:
            """"""
            try:
                new_datetime = datetime.datetime.combine(current_date,
                                                         current_time)
            except:
                return

            set_data(new_datetime)

        def get_date() -> datetime.date:
            """"""
            return current_date

        def set_date(new_date: datetime.date) -> None:
            """"""
            nonlocal current_date
            current_date = new_date
            update_datetime()

        def get_time() -> datetime.time:
            """"""
            return current_time

        def set_time(new_time: datetime.time) -> None:
            """"""
            nonlocal current_time
            current_time = new_time
            update_datetime()

        self._date = NodeDatePicker(get_date, set_date)
        self._time = NodeTimePicker(get_time, set_time)

        self.append(self._date)
        self.append(self._time)

    def set_data(self,
                 value: str,
                 ) ->   None:
        """"""
        from datetime import datetime
        value = datetime.fromisoformat(value)
        self._date.set_data(value.date().isoformat())
        self._time.set_data(value.time().isoformat())