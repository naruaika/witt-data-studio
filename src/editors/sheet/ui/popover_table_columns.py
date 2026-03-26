# popover_table_columns.py
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
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Pango

from ....core.models.table import DataTable

from .formula_bar import SheetFormulaBar

class SheetTableColumnListItem(GObject.Object):

    __gtype_name__ = 'SheetTableColumnListItem'

    cname = GObject.Property(type = str, default = '')
    dtype = GObject.Property(type = str, default = '')

    def __init__(self,
                 cname: str,
                 dtype: str,
                 ) ->   None:
        """"""
        super().__init__()

        self.cname = cname
        self.dtype = dtype


@Gtk.Template(resource_path = '/com/wittara/studio/editors/sheet/ui/popover_table_columns.ui')
class SheetTableColumnsPopover(Gtk.Popover):

    __gtype_name__ = 'SheetTableColumnsPopover'

    SearchEntry = Gtk.Template.Child()
    ListView    = Gtk.Template.Child()
    Selection   = Gtk.Template.Child()

    def __init__(self,
                 formula_bar: SheetFormulaBar,
                 ) ->         None:
        """"""
        super().__init__()

        self.formula_bar = formula_bar

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
        button.add_css_class('button-sm')
        list_item.set_child(button)

        box = Gtk.Box(orientation   = Gtk.Orientation.HORIZONTAL,
                      margin_top    = 6,
                      margin_bottom = 6,
                      margin_start  = 6,
                      margin_end    = 6)
        button.set_child(box)
        button.add_css_class('font-normal')

        dragger = Gtk.Image(icon_name  = 'list-drag-handle-symbolic',
                            margin_end = 6)
        dragger.add_css_class('dimmed')
        box.append(dragger)

        cname = Gtk.Label(xalign     = 0.0,
                          hexpand    = True,
                          ellipsize  = Pango.EllipsizeMode.END,
                          margin_end = 10)
        box.append(cname)

        dtype = Gtk.Label()
        dtype.add_css_class('dimmed')
        box.append(dtype)

        list_item.dragger = dragger
        list_item.cname = cname
        list_item.dtype = dtype
        list_item.handler = None

    def _bind_list_factory(self,
                           list_item_factory: Gtk.SignalListItemFactory,
                           list_item:         Gtk.ListItem,
                           ) ->               None:
        """"""
        item_data = list_item.get_item()

        button = list_item.get_child()
        button.set_tooltip_text(item_data.cname)

        if item_data.cname == self.column_name:
            button.add_css_class('accent')
            button.remove_css_class('flat')
        else:
            button.remove_css_class('accent')
            button.add_css_class('flat')

        list_item.cname.set_label(item_data.cname)
        list_item.dtype.set_label(item_data.dtype)

        is_searching = self.SearchEntry.get_text() != ''
        list_item.dragger.set_visible(not is_searching)

        def on_clicked(button: Gtk.Button) -> None:
            """"""
            self.popdown()

            editor = self.formula_bar.get_editor()
            editor.select_table_column(self.table_name,
                                       item_data.cname)
            editor.grab_focus()

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
        editor = self.formula_bar.get_editor()
        active = editor.selection.current_active_cell

        lcolumn = editor.display.get_lcolumn_from_column(active.column)
        lrow    = editor.display.get_lrow_from_row(active.row)

        table, column_name = \
            editor.document.get_table_column_by_position(lcolumn, lrow)

        self.table_name = table.tname
        self.column_name = column_name

        if (
            not isinstance(table, DataTable) or
            not table.with_header            or
            table.placeholder
        ):
            self.ListStore = None
            self.Selection.set_model(None)
            return

        query = self.SearchEntry.get_text()

        self.ListStore = Gio.ListStore.new(SheetTableColumnListItem)

        for cname, dtype in table.schema.items():
            if query.lower() not in cname.lower():
                continue
            dtype = dtype.__class__.__name__
            list_item = SheetTableColumnListItem(cname, dtype)
            self.ListStore.append(list_item)

        self.Selection.set_model(self.ListStore)
