# file_reader.py
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

class NodeFileReader(Gtk.Button):

    __gtype_name__ = 'NodeFileReader'

    def __init__(self,
                 get_data: callable,
                 set_data: callable,
                 ) ->      None:
        """"""
        box = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL,
                      spacing     = 6)

        label = Gtk.Label(label     = get_data() or _('Choose File...'),
                          xalign    = 0.0,
                          hexpand   = True,
                          ellipsize = Pango.EllipsizeMode.END)
        box.append(label)

        icon = Gtk.Image(icon_name = 'folder-open-symbolic')
        box.append(icon)

        super().__init__(child = box)

        self._get_data = get_data
        self._set_data = set_data

        self.connect('clicked', self._on_clicked)

    def _on_clicked(self,
                    button: Gtk.Button,
                    ) ->    None:
        """"""
        window = self.get_root()

        from ....ui.file_dialog import FileDialog
        FileDialog.open(window, self._set_data)

    def set_data(self,
                 value: str,
                 ) ->   None:
        """"""
        box = self.get_child()
        label = box.get_first_child()

        if value:
            label.set_label(value)
            label.set_ellipsize(Pango.EllipsizeMode.START)
        else:
            label.set_label(_('Choose File...'))
            label.set_ellipsize(Pango.EllipsizeMode.END)

        self.set_tooltip_text(value)