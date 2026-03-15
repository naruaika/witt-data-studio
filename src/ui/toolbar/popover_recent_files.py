# popover_recent_files.py
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
from os.path       import basename

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