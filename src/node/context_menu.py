# context_menu.py
#
# Copyright 2025 Naufan Rusyda Faikar
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

from gi.repository import Gio
from gi.repository import GLib
from gi.repository import Gtk
import gc


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
            def do_remove() -> None:
                """"""
                popover.unparent()
                gc.collect()

            GLib.timeout_add(1000, do_remove)

        self.connect('closed', on_closed)
