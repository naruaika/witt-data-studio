# check_button.py
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
from gi.repository import Pango

class NodeCheckButton(Gtk.CheckButton):

    __gtype_name__ = 'NodeCheckButton'

    def __init__(self,
                 title:    str,
                 get_data: callable,
                 set_data: callable,
                 ) ->      None:
        """"""
        label = Gtk.Label(label        = title,
                          xalign       = 0.0,
                          hexpand      = True,
                          ellipsize    = Pango.EllipsizeMode.END,
                          tooltip_text = title)

        super().__init__(active = get_data(),
                         child  = label)

        self._get_data = get_data
        self._set_data = set_data

        self.handler = self.connect('toggled', self._on_toggled)

    def _on_toggled(self,
                    button: Gtk.CheckButton,
                    ) ->    None:
        """"""
        active = button.get_active()
        self._set_data(active)

    def set_data(self,
                 value: bool,
                 ) ->   None:
        """"""
        self.handler_block(self.handler)
        self.set_active(value)
        self.handler_unblock(self.handler)