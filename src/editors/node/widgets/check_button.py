# check_button.py
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