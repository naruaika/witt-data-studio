# check_group.py
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

from copy          import deepcopy
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