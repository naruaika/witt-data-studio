# context_menu.py
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

from gi.repository import Gio
from gi.repository import GLib
from gi.repository import Gtk

class NodeContextMenu(Gtk.PopoverMenu):

    __gtype_name__ = 'NodeContextMenu'

    def __init__(self) -> None:
        """"""
        menu = Gio.Menu.new()

        super().__init__(halign     = Gtk.Align.START,
                         vexpand    = True,
                         has_arrow  = False,
                         menu_model = menu)

        def on_closed(popover: Gtk.PopoverMenu) -> None:
            """"""
            GLib.timeout_add(250, popover.unparent)

        self.connect('closed', on_closed)
