# datetime_picker.py
#
# Copyright 2025 Naufan Rusyda Faikar <hello@naruaika.me>
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