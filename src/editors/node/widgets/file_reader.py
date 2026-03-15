# file_reader.py
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