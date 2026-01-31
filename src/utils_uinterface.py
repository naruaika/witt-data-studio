# utils_uinterface.py
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

from gi.repository import Gio
from gi.repository import GObject
from gi.repository import Gtk

class AutoSeparatorModel(GObject.Object, Gio.ListModel, Gtk.SectionModel):

    __gtype_name__ = 'AutoSeparatorModel'

    def __init__(self,
                 items: list[str],
                 ) ->   None:
        """"""
        super().__init__()

        display_items   = [x for x in items if x != '---']
        self.list_store = Gtk.StringList.new(display_items)
        self.sections   = []

        count = 0
        start = 0
        for item in items:
            if item == '---':
                if count > 0:
                    section = (start, start + count)
                    self.sections.append(section)
                    start += count
                    count = 0
            else:
                count += 1
        if count > 0:
            section = (start, start + count)
            self.sections.append(section)

    def do_get_section(self,
                       position: int,
                       ) ->      None:
        """"""
        for i, (start, end) in enumerate(self.sections):
            if start <= position < end:
                return i, start, end
        return 0, 0, 0

    def do_get_item(self,
                    position: int,
                    ) ->      None:
        """"""
        return self.list_store.get_item(position)

    def do_get_n_items(self) -> None:
        """"""
        return self.list_store.get_n_items()

    def do_get_item_type(self) -> None:
        """"""
        return GObject.TYPE_OBJECT
