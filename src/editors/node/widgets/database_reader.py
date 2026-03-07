# database_reader.py
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

class NodeDatabaseReader(Gtk.Button):

    __gtype_name__ = 'NodeDatabaseReader'

    def __init__(self,
                 get_data: callable,
                 set_data: callable,
                 ) ->      None:
        """"""
        label = Gtk.Label(label            = get_data()['query'],
                          xalign           = 0.0,
                          ellipsize        = Pango.EllipsizeMode.END,
                          single_line_mode = True)
        label.add_css_class('monospace')

        super().__init__(child = label)

        self._get_data = get_data
        self._set_data = set_data

        self.connect('clicked', self._on_clicked)

    def _on_clicked(self,
                    button: Gtk.Button,
                    ) ->   None:
        """"""
        data = self._get_data()

        window = self.get_root()
        application = window.get_application()

        from ....ui.database_import.widget import DatabaseImportWindow
        importer = DatabaseImportWindow(query         = data['query'],
                                        config        = data['config'],
                                        callback      = self._set_data,
                                        transient_for = window,
                                        application   = application)
        importer.present()

    def set_data(self,
                 value: str,
                 ) ->   None:
        """"""
        label = self.get_child()
        label.set_label(str(value))