# radio.py
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

class NodeRadioGroup(Gtk.Box):

    __gtype_name__ = 'NodeRadioGroup'

    def __init__(self,
                 get_data: callable,
                 set_data: callable,
                 options:  dict,
                 ) ->      None:
        """"""
        super().__init__(orientation = Gtk.Orientation.VERTICAL,
                         homogeneous = True,
                         hexpand     = True)
        self.add_css_class('linked')

        self._get_data = get_data
        self._set_data = set_data
        self._options  = options

        self._populate_ui()

    def _populate_ui(self) -> None:
        """"""
        group = None

        selected = self._get_data()

        for key, val in self._options.items():
            button = Gtk.CheckButton(label   = val,
                                     hexpand = True)
            self.append(button)

            if group:
                button.set_group(group)
            else:
                group = button

            if key == selected:
                button.set_active(True)

            button.connect('toggled', self._on_toggled)

    def _on_toggled(self,
                    button: Gtk.CheckButton,
                    ) ->    None:
        """"""
        if button.get_active():
            value = button.get_label()
            key = next((k for k, v in self._options.items() if v == value), '')
            self._set_data(key)