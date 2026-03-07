# check_group.py
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

from copy import deepcopy
from gi.repository import Gtk
from gi.repository import Pango

class NodeCheckGroup(Gtk.Box):

    __gtype_name__ = 'NodeCheckGroup'

    def __init__(self,
                 get_data: callable,
                 set_data: callable,
                 options:  list[str],
                 ) ->      None:
        """"""
        super().__init__(orientation = Gtk.Orientation.VERTICAL)
        self.add_css_class('linked')

        self._get_data = get_data
        self._set_data = set_data
        self._options  = options

        self._populate_ui()

    def _populate_ui(self) -> None:
        """"""
        for value in self._options:
            label = Gtk.Label(halign       = Gtk.Align.START,
                              valign       = Gtk.Align.CENTER,
                              hexpand      = True,
                              ellipsize    = Pango.EllipsizeMode.END,
                              label        = value,
                              tooltip_text = value)
            active = value in self._get_data()

            check = Gtk.CheckButton(child  = label,
                                    active = active)
            self.append(check)

            check.connect('toggled', self._on_toggled, value)

    def _on_toggled(self,
                    button: Gtk.CheckButton,
                    value:  str,
                    ) ->    None:
        """"""
        selected = deepcopy(self._get_data())

        if button.get_active():
            selected.append(value)
        else:
            selected.remove(value)

        self._set_data(selected)