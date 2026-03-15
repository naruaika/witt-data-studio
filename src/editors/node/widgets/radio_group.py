# radio.py
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