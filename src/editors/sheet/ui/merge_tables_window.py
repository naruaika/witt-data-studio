# merge_tables_window.py
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

from gi.repository import Adw
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Pango

from ..editor import SheetEditor

STRATEGY_OPTS = {'inner': _('Inner'),
                 'left':  _('Left'),
                 'right': _('Right'),
                 'full':  _('Full'),
                 'cross': _('Cross'),
                 'semi':  _('Semi'),
                 'anti':  _('Anti')}

ORDER_OPTS = {'none':       _('None'),
              'left':       _('Left'),
              'right':      _('Right'),
              'left_right': _('Left-Right'),
              'right_left': _('Right-Left')}

@Gtk.Template(resource_path = '/com/wittara/studio/editors/sheet/ui/merge_tables_window.ui')
class SheetMergeTablesWindow(Adw.Window):

    __gtype_name__ = 'SheetMergeTablesWindow'

    SplitView        = Gtk.Template.Child()

    SidebarHeaderBar = Gtk.Template.Child()
    ContentHeaderBar = Gtk.Template.Child()
    WindowTitle      = Gtk.Template.Child()

    LeftTableRow     = Gtk.Template.Child()
    LeftColumnRow    = Gtk.Template.Child()
    LeftColumnsRow   = Gtk.Template.Child()
    RightTableRow    = Gtk.Template.Child()
    RightColumnRow   = Gtk.Template.Child()
    RightColumnsRow  = Gtk.Template.Child()
    StrategyRow      = Gtk.Template.Child()
    MaintainOrderRow = Gtk.Template.Child()

    OutputView       = Gtk.Template.Child()
    MergeButton      = Gtk.Template.Child()

    def __init__(self,
                 tname:    str,
                 tables:   list,
                 callback: callable,
                 **kwargs: dict,
                 ) ->      None:
        """"""
        super().__init__(**kwargs)

        self.tname    = tname
        self.tables   = tables
        self.callback = callback

        self._setup_uinterfaces()
        self._setup_controllers()

    def _setup_uinterfaces(self) -> None:
        """"""
        self._setup_output_viewer()
        self._setup_properties_box()
        self._setup_sidebar_toggle_button()

    def _setup_output_viewer(self) -> None:
        """"""
        self.Editor = SheetEditor(prefer_synchro = True,
                                  view_read_only = True)
        self.OutputView.set_child(self.Editor)

    def _setup_properties_box(self) -> None:
        """"""
        self.LeftColumnsRow.selected = []
        self.RightColumnsRow.selected = []

        model = Gtk.StringList()
        for tname, _ in self.tables:
            model.append(tname)
        self.LeftTableRow.set_model(model)

        model = Gtk.StringList()
        for tname, _ in self.tables:
            model.append(tname)
        self.RightTableRow.set_model(model)

        position = next((i for i, (tname, _) in enumerate(self.tables)
                           if tname == self.tname))
        self.LeftTableRow.set_selected(position)
        self.RightTableRow.set_selected(position)

        model = Gtk.StringList()
        for separator in STRATEGY_OPTS.values():
            model.append(separator)
        self.StrategyRow.set_model(model)

        model = Gtk.StringList()
        for separator in ORDER_OPTS.values():
            model.append(separator)
        self.MaintainOrderRow.set_model(model)

    def _setup_sidebar_toggle_button(self) -> None:
        """"""
        close_button = Gtk.Button(icon_name = 'go-previous-symbolic',
                                  visible   = False)
        self.SidebarHeaderBar.pack_start(close_button)

        def on_sidebar_closed(button: Gtk.Button) -> None:
            """"""
            self.SplitView.set_show_sidebar(False)

        close_button.connect('clicked', on_sidebar_closed)

        visible = self.SplitView.get_collapsed()
        active = self.SplitView.get_show_sidebar()
        toggle_button = Gtk.ToggleButton(icon_name = 'sidebar-show-symbolic',
                                         active    = active,
                                         visible   = visible)
        self.ContentHeaderBar.pack_start(toggle_button)

        def on_sidebar_toggled(button: Gtk.ToggleButton) -> None:
            """"""
            toggled = button.get_active()
            self.SplitView.set_show_sidebar(toggled)

        toggle_button.connect('toggled', on_sidebar_toggled)

        def on_view_collapsed(split_view: Adw.OverlaySplitView,
                              param_spec: GObject.ParamSpec,
                              ) ->        None:
            """"""
            visible = self.SplitView.get_collapsed()
            close_button.set_visible(visible)
            toggle_button.set_visible(visible)

        self.SplitView.connect('notify::collapsed', on_view_collapsed)

        def on_view_show_sidebar(split_view: Adw.OverlaySplitView,
                                 param_spec: GObject.ParamSpec,
                                 ) ->        None:
            """"""
            show_sidebar = split_view.get_show_sidebar()
            toggle_button.set_active(show_sidebar)

        self.SplitView.connect('notify::show-sidebar', on_view_show_sidebar)

    def _setup_controllers(self) -> None:
        """"""
        controller = Gtk.EventControllerKey()
        controller.connect('key-pressed', self._on_key_pressed)
        self.add_controller(controller)

    def _on_key_pressed(self,
                        event:   Gtk.EventControllerKey,
                        keyval:  int,
                        keycode: int,
                        state:   Gdk.ModifierType,
                        ) ->     bool:
        """"""
        if state & Gdk.ModifierType.CONTROL_MASK and \
                keyval == Gdk.KEY_Escape:
            self.close()
            return Gdk.EVENT_STOP

        return Gdk.EVENT_PROPAGATE

    @Gtk.Template.Callback()
    def _on_left_table_changed(self, *args) -> None:
        """"""
        self.LeftColumnsRow.selected = []

        selected = self.LeftTableRow.get_selected()
        _, table = self.tables[selected]

        columns = table.collect_schema().names()

        model = Gtk.StringList()
        for option in columns:
            model.append(option)
        self.LeftColumnRow.set_model(model)

    @Gtk.Template.Callback()
    def _on_left_column_changed(self, *args) -> None:
        """"""
        selected = self.LeftTableRow.get_selected()
        _, table = self.tables[selected]

        columns = table.collect_schema().names()

        exclude = self.LeftColumnRow.get_selected_item()
        exclude = exclude.get_string()
        columns.remove(exclude)

        self._populate_columns_row(self.LeftColumnsRow, columns)

        self._refresh_output_viewer()

    @Gtk.Template.Callback()
    def _on_right_table_changed(self, *args) -> None:
        """"""
        self.RightColumnsRow.selected = []

        selected = self.RightTableRow.get_selected()
        _, table = self.tables[selected]

        columns = table.collect_schema().names()

        model = Gtk.StringList()
        for option in columns:
            model.append(option)
        self.RightColumnRow.set_model(model)

    @Gtk.Template.Callback()
    def _on_right_column_changed(self, *args) -> None:
        """"""
        selected = self.RightTableRow.get_selected()
        _, table = self.tables[selected]

        columns = table.collect_schema().names()

        exclude = self.RightColumnRow.get_selected_item()
        exclude = exclude.get_string()
        columns.remove(exclude)

        self._populate_columns_row(self.RightColumnsRow, columns)

        self._refresh_output_viewer()

    @Gtk.Template.Callback()
    def _on_strategy_changed(self, *args) -> None:
        """"""
        self._refresh_output_viewer()

    @Gtk.Template.Callback()
    def _on_maintain_order_changed(self, *args) -> None:
        """"""
        self._refresh_output_viewer()

    def _populate_columns_row(self,
                              widget:  Gtk.FlowBox,
                              columns: list,
                              checked: bool = True,
                              ) ->     None:
        """"""
        def on_check_toggled(button:  Gtk.CheckButton,
                             value:   str,
                             is_meta: bool = False,
                             ) ->     None:
            """"""
            if is_meta:
                # Very not efficient, because this'll
                # call _populate_columns_row() twice.
                # But anyway it does the job; TODO
                widget.selected = []
                checked = button.get_active()
                self._populate_columns_row(widget, columns, checked)
                self._refresh_output_viewer()
                return

            selected = widget.selected
            selected.append(value) if button.get_active() \
                                   else selected.remove(value)
            widget.selected = selected
            self._refresh_output_viewer()

        widget.remove_all()

        _columns = [_('Select All')] + columns

        for cidx, column in enumerate(_columns):
            label = Gtk.Label(halign       = Gtk.Align.START,
                              valign       = Gtk.Align.CENTER,
                              hexpand      = True,
                              ellipsize    = Pango.EllipsizeMode.END,
                              label        = column,
                              tooltip_text = column)
            check = Gtk.CheckButton(active        = checked,
                                    margin_top    = 2,
                                    margin_bottom = 2,
                                    margin_start  = 2,
                                    margin_end    = 2)
            check.set_child(label)
            widget.append(check)
            is_meta = cidx == 0
            check.connect('toggled', on_check_toggled, column, is_meta)

        widget.selected = columns if checked else []

    def _refresh_output_viewer(self) -> None:
        """"""
        selected = self.LeftTableRow.get_selected()
        if selected == Gtk.INVALID_LIST_POSITION:
            return
        __, ltable = self.tables[selected]

        selected = self.RightTableRow.get_selected()
        if selected == Gtk.INVALID_LIST_POSITION:
            return
        __, rtable = self.tables[selected]

        lcolumn = self.LeftColumnRow.get_selected_item()
        if not lcolumn:
            return
        lcolumn = lcolumn.get_string()

        rcolumn = self.RightColumnRow.get_selected_item()
        if not rcolumn:
            return
        rcolumn = rcolumn.get_string()

        how = self.StrategyRow.get_selected_item()
        if not how:
            return
        how = how.get_string()
        how = next((k for k, v in STRATEGY_OPTS.items() if v == how))

        order = self.MaintainOrderRow.get_selected_item()
        if not order:
            return
        order = order.get_string()
        order = next((k for k, v in ORDER_OPTS.items() if v == order))

        lcolumns = self.LeftColumnsRow.selected \
                   or ltable.collect_schema().names()
        rcolumns = self.RightColumnsRow.selected \
                   or rtable.collect_schema().names()

        if lcolumn not in lcolumns:
            lcolumns = [lcolumn] + lcolumns
        if rcolumn not in rcolumns:
            rcolumns = [rcolumn] + rcolumns

        ltable = ltable.lazy().select(lcolumns)
        rtable = rtable.lazy().select(rcolumns)

        if ltable.serialize() != rtable.serialize():
            table = ltable.join(other          = rtable,
                                left_on        = lcolumn,
                                right_on       = rcolumn,
                                how            = how,
                                maintain_order = order)
        else:
            table = ltable
        table = table.head(1_000)

        tables = {_('Table'): ((1, 1), table)}
        self.Editor.set_data(tables)

    @Gtk.Template.Callback()
    def _on_merge_button_clicked(self,
                                 button: Gtk.Button,
                                 ) ->    None:
        """"""
        selected = self.LeftTableRow.get_selected()
        ltname, ltable = self.tables[selected]

        selected = self.RightTableRow.get_selected()
        rtname, rtable = self.tables[selected]

        lcolumn = self.LeftColumnRow.get_selected_item()
        lcolumn = lcolumn.get_string()

        rcolumn = self.RightColumnRow.get_selected_item()
        rcolumn = rcolumn.get_string()

        how = self.StrategyRow.get_selected_item()
        how = how.get_string()
        how = next((k for k, v in STRATEGY_OPTS.items() if v == how))

        order = self.MaintainOrderRow.get_selected_item()
        order = order.get_string()
        order = next((k for k, v in ORDER_OPTS.items() if v == order))

        lcolumns = self.LeftColumnsRow.selected \
                   or ltable.collect_schema().names()
        rcolumns = self.RightColumnsRow.selected \
                   or rtable.collect_schema().names()

        if lcolumn not in lcolumns:
            lcolumns = [lcolumn] + lcolumns
        if rcolumn not in rcolumns:
            rcolumns = [rcolumn] + rcolumns

        self.close()
        self.callback([ltname, lcolumn, lcolumns,
                       rtname, rcolumn, rcolumns,
                       how, order])
