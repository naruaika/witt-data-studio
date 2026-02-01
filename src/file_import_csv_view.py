# file_import_csv_view.py
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
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Pango
from sys import float_info

SEPARATOR_OPTS = {'\t': _('Tab'),
                  ';':  _('Semicolon'),
                  ',':  _('Comma'),
                  ' ':  _('Space'),
                  '|':  _('Pipe')}

QUOTE_CHAR_OPTS = {'"': _('Double'),
                   "'": _('Single')}

DECIMAL_COMMA_OPTS = {False: _('Period'),
                      True:  _('Comma')}


class FileImportCsvView(GObject.Object):

    __gtype_name__ = 'FileImportCsvView'

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
        self.all_columns      = columns
        self.refresh_ui       = refresh_ui
        self.column_toggled   = column_toggled

        self._setup_separators_group()
        self._setup_rows_group()
        self._setup_header_group()
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

    def _setup_separators_group(self) -> None:
        """"""
        group = Adw.PreferencesGroup(title = _('How to Read File?'))
        self.preferences_page.add(group)


        model = Gtk.StringList()
        for separator in SEPARATOR_OPTS.values():
            model.append(separator)
        separator = Adw.ComboRow(title = _('Column Separator'),
                                 model = model)
        group.add(separator)

        try:
            keys = list(SEPARATOR_OPTS.keys())
            selected = keys.index(self.default_args['separator'])
            separator.set_selected(selected)
        except:
            pass

        model = Gtk.StringList()
        for quote_char in QUOTE_CHAR_OPTS.values():
            model.append(quote_char)
        quote_char = Adw.ComboRow(title = _('Quote Character'),
                                  model = model)
        group.add(quote_char)

        model = Gtk.StringList()
        for decimal_comma in DECIMAL_COMMA_OPTS.values():
            model.append(decimal_comma)
        decimal_comma = Adw.ComboRow(title = _('Decimal Separator'),
                                     model = model)
        group.add(decimal_comma)

        separator.connect('notify::selected', self._on_input_changed)
        quote_char.connect('notify::selected', self._on_input_changed)
        decimal_comma.connect('notify::selected', self._on_input_changed)

        self.conf_widgets['separator']     = separator
        self.conf_widgets['quote_char']    = quote_char
        self.conf_widgets['decimal_comma'] = decimal_comma

        # Hide separators group for TSV file
        if self.default_args['separator'] == '\t':
            group.set_visible(False)

    def _setup_rows_group(self) -> None:
        """"""
        group = Adw.PreferencesGroup(title = _('Which Rows to Pick?'))
        self.preferences_page.add(group)

        adjustment = Gtk.Adjustment(value          = 0,
                                    lower          = 0,
                                    upper          = float_info.max,
                                    step_increment = 1,
                                    page_increment = 10,
                                    page_size      = 10)
        n_rows = Adw.SpinRow(title      = _('No. Rows'),
                             adjustment = adjustment)
        group.add(n_rows)

        adjustment = Gtk.Adjustment(value          = 1,
                                    lower          = 1,
                                    upper          = float_info.max,
                                    step_increment = 1,
                                    page_increment = 10,
                                    page_size      = 10)
        from_row = Adw.SpinRow(title      = _('From Row'),
                               adjustment = adjustment)
        group.add(from_row)

        from_row.connect('notify::value', self._on_input_changed)
        n_rows.connect('notify::value', self._on_input_changed)

        self.conf_widgets['from_row'] = from_row
        self.conf_widgets['n_rows']   = n_rows

    def _setup_header_group(self) -> None:
        """"""
        group = Adw.PreferencesGroup()
        self.preferences_page.add(group)

        has_header = Adw.SwitchRow(title  = _('First Row as Header'),
                                   active = True)
        group.add(has_header)

        has_header.connect('notify::active', self._on_input_changed)

        self.conf_widgets['has_header'] = has_header

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

        def get_selected() -> list[str] | None:
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
            check = Gtk.CheckButton(active        = checked,
                                    margin_top    = 2,
                                    margin_bottom = 2,
                                    margin_start  = 2,
                                    margin_end    = 2)
            check.set_child(label)
            self.ColumnFlowBox.append(check)
            is_meta = cidx == 0
            check.connect('toggled', on_check_toggled, column, is_meta)

        self.ColumnFlowBox.selected = self.columns if checked else []

    def _on_input_changed(self,
                          widget:     Gtk.Widget,
                          param_spec: GObject.ParamSpec,
                          ) ->        None:
        """"""
        self.refresh_ui()