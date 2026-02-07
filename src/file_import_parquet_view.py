# file_import_parquet_view.py
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

from gi.repository import Adw
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Pango

class FileImportParquetView(GObject.Object):

    __gtype_name__ = 'FileImportParquetView'

    def __init__(self,
                 preferences_page: Adw.PreferencesPage,
                 default_args:     dict,
                 conf_widgets:     dict,
                 columns:          list[str],
                 refresh_ui:       callable,
                 column_toggled:   callable,
                 ) ->              None:
        """"""
        super().__init__()

        self.preferences_page = preferences_page
        self.default_args     = default_args
        self.conf_widgets     = conf_widgets
        self.columns          = columns
        self.refresh_ui       = refresh_ui
        self.column_toggled   = column_toggled

        self._setup_rows_group()
        self._setup_columns_group()

    def update_columns(self,
                       columns: list[str],
                       ) ->     None:
        """"""
        self.columns = columns

        if len(columns) == 1:
            self.ColumnFlowBox.set_min_children_per_line(1)
        else:
            self.ColumnFlowBox.set_min_children_per_line(2)

        self._populate_column_flow_box()

    def _setup_rows_group(self) -> None:
        """"""
        group = Adw.PreferencesGroup(title = _('Which Rows to Pick?'))
        self.preferences_page.add(group)

        adjustment = Gtk.Adjustment(value          = 0,
                                    lower          = 0,
                                    upper          = GLib.MAXDOUBLE,
                                    step_increment = 1,
                                    page_increment = 10,
                                    page_size      = 10)
        n_rows = Adw.SpinRow(title      = _('No. Rows'),
                             adjustment = adjustment)
        group.add(n_rows)

        n_rows.connect('notify::value', self._on_input_changed)

        self.conf_widgets['n_rows'] = n_rows

    def _setup_columns_group(self) -> None:
        """"""
        group = Adw.PreferencesGroup(title = _('Which Columns to Pick?'))
        self.preferences_page.add(group)

        row = Adw.PreferencesRow()
        row.set_activatable(False)
        group.add(row)

        self.ColumnFlowBox = Gtk.FlowBox(selection_mode        = Gtk.SelectionMode.NONE,
                                         homogeneous           = True,
                                         min_children_per_line = 2,
                                         margin_top            = 6,
                                         margin_bottom         = 6,
                                         margin_start          = 4,
                                         margin_end            = 4,
                                         column_spacing        = 4,
                                         row_spacing           = 4)
        self.ColumnFlowBox.add_css_class('navigation-sidebar')
        row.set_child(self.ColumnFlowBox)

        def get_selected() -> list[str]:
            """"""
            return self.ColumnFlowBox.selected
        self.ColumnFlowBox.selected = self.columns
        self.ColumnFlowBox.get_selected = get_selected

        self._populate_column_flow_box()

        self.conf_widgets['columns'] = self.ColumnFlowBox

    def _populate_column_flow_box(self,
                                  checked: bool = True,
                                  ) ->     None:
        """"""
        def on_check_toggled(button:  Gtk.CheckButton,
                             value:   str,
                             is_meta: bool = False,
                             ) ->     None:
            """"""
            if is_meta:
                # Very not efficient, because this will
                # call _populate_column_flow_box() twice.
                # But anyway it does the job.
                self.ColumnFlowBox.selected = []
                self.refresh_ui()
                checked = button.get_active()
                self._populate_column_flow_box(checked)
                return

            selected = self.ColumnFlowBox.selected
            selected.append(value) if button.get_active() \
                                   else selected.remove(value)
            self.ColumnFlowBox.selected = selected
            self.column_toggled()

        self.ColumnFlowBox.remove_all()

        columns = [_('Select All')] + self.columns

        for cidx, column in enumerate(columns):
            label = Gtk.Label(halign       = Gtk.Align.START,
                              valign       = Gtk.Align.CENTER,
                              hexpand      = True,
                              ellipsize    = Pango.EllipsizeMode.END,
                              label        = column,
                              tooltip_text = column)
            check_button = Gtk.CheckButton(active        = checked,
                                           margin_top    = 2,
                                           margin_bottom = 2,
                                           margin_start  = 2,
                                           margin_end    = 2)
            check_button.set_child(label)
            self.ColumnFlowBox.append(check_button)
            is_meta = cidx == 0
            check_button.connect('toggled', on_check_toggled, column, is_meta)

        self.ColumnFlowBox.selected = self.columns if checked else []

    def _on_input_changed(self,
                          widget:     Gtk.Widget,
                          param_spec: GObject.ParamSpec,
                          ) ->        None:
        """"""
        self.refresh_ui()