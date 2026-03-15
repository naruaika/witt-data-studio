# popover_recent_files.py
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
from os.path import basename

@Gtk.Template(resource_path = '/com/wittara/studio/ui/toolbar/popover_recent_files.ui')
class RecentFilesPopover(Gtk.Popover):

    __gtype_name__ = 'RecentFilesPopover'

    SearchEntry = Gtk.Template.Child()
    ListView    = Gtk.Template.Child()
    Selection   = Gtk.Template.Child()

    def __init__(self) -> None:
        """"""
        super().__init__()

        factory = Gtk.SignalListItemFactory()
        factory.connect('setup', self._setup_list_factory)
        factory.connect('bind', self._bind_list_factory)
        self.ListView.set_factory(factory)

    def _setup_list_factory(self,
                            list_item_factory: Gtk.SignalListItemFactory,
                            list_item:         Gtk.ListItem,
                            ) ->               None:
        """"""
        list_item.set_activatable(False)

        button = Gtk.Button()
        button.add_css_class('flat')
        list_item.set_child(button)

        box = Gtk.Box(orientation   = Gtk.Orientation.VERTICAL,
                      margin_top    = 6,
                      margin_bottom = 6,
                      margin_start  = 10,
                      margin_end    = 10)
        button.set_child(box)

        head = Gtk.Label(xalign    = 0.0,
                         ellipsize = Pango.EllipsizeMode.END)
        box.append(head)

        body = Gtk.Label(xalign    = 0.0,
                         ellipsize = Pango.EllipsizeMode.END)
        body.add_css_class('caption')
        body.add_css_class('dimmed')
        box.append(body)

        list_item.head = head
        list_item.body = body
        list_item.handler = None

    def _bind_list_factory(self,
                           list_item_factory: Gtk.SignalListItemFactory,
                           list_item:         Gtk.ListItem,
                           ) ->               None:
        """"""
        item_data = list_item.get_item()
        file_path = item_data.get_string()

        button = list_item.get_child()
        button.set_tooltip_text(file_path)

        filename = basename(file_path)
        list_item.head.set_label(filename)

        list_item.body.set_label(file_path)

        def on_clicked(button: Gtk.Button) -> None:
            """"""
            self.popdown()

            window = self.get_root()
            application = window.get_application()
            application.load_file(file_path)

        if list_item.handler:
            list_item.disconnect(list_item.handler)

        list_item.handler = button.connect('clicked', on_clicked)

    def do_map(self) -> None:
        """"""
        self._populate_ui()

        Gtk.Popover.do_map(self)

    @Gtk.Template.Callback()
    def _on_search_entry_changed(self,
                                 entry: Gtk.SearchEntry,
                                 ) ->   None:
        """"""
        self._populate_ui()

    def _populate_ui(self) -> None:
        """"""
        window = self.get_root()
        application = window.get_application()

        recent_files = application.get_recent_file_list()

        query = self.SearchEntry.get_text()

        model = Gtk.StringList()
        for file_path in recent_files:
            if query not in file_path:
                continue
            model.append(file_path)
        self.Selection.set_model(model)