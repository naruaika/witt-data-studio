# date_picker.py
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
