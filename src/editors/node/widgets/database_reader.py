# database_reader.py
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