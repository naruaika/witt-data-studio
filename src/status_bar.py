# status_bar.py
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

from gi.repository import Gtk
from gi.repository import Pango
from locale import format_string

from .node.editor import NodeEditor
from .chart.editor import ChartEditor
from .sheet.editor import SheetEditor

from .core.datatable import DataTable

@Gtk.Template(resource_path = '/com/macipra/witt/status_bar.ui')
class StatusBar(Gtk.Box):

    __gtype_name__ = 'StatusBar'

    BoundaryContext = Gtk.Template.Child()
    SceneSelections = Gtk.Template.Child()
    SceneStatistics = Gtk.Template.Child()

    def __init__(self) -> None:
        """"""
        self._mapping = [
            (
                self.BoundaryContext,
                (
                    SheetEditor,
                ),
            ),
            (
                self.SceneSelections,
                (
                    NodeEditor,
                    SheetEditor,
                ),
            ),
            (
                self.SceneStatistics,
                (
                    NodeEditor,
                    SheetEditor,
                ),
            ),
        ]

    def populate(self) -> None:
        """"""
        window = self.get_root()
        editor = window.get_selected_editor()

        for widget, owners in self._mapping:
            if not isinstance(editor, owners):
                widget.set_visible(False)
                continue
            widget.set_visible(True)

        if isinstance(editor, NodeEditor):
            n_selected = len(editor.selected_nodes)

            if n_selected > 0:
                label = f'{format_string('%d', n_selected, grouping = True)} {_('selected')}'
                self.SceneSelections.set_label(label)
            else:
                self.SceneSelections.set_visible(False)

            label = f'{_('Nodes')}: {format_string('%d', len(editor.nodes), grouping = True)}, ' \
                    f'{_('Links')}: {format_string('%d', len(editor.links), grouping = True)}'
            self.SceneStatistics.set_label(label)

        if isinstance(editor, SheetEditor):
            acell = editor.selection.current_active_cell
            lcol = editor.display.get_lcolumn_from_column(acell.column)
            lrow = editor.display.get_lrow_from_row(acell.row)

            table = editor.document.get_table_by_position(lcol, lrow)

            if isinstance(table, DataTable):
                n_rows = table.bounding_box.row_span
                n_cols = table.bounding_box.column_span
                row_unit = _('rows') if n_rows else _('row')
                col_unit = _('columns') if n_cols else _('row')
                label = f'{table.tname}: ' \
                        f'{format_string('%d', n_rows, grouping = True)} {row_unit} x ' \
                        f'{format_string('%d', n_cols, grouping = True)} {col_unit}'
                self.BoundaryContext.set_label(label)
            else:
                self.BoundaryContext.set_visible(False)

            arange = editor.selection.current_active_range
            n_selected = arange.column_span * arange.row_span

            if n_selected == 1:
                label = f'{editor.selection.current_cell_name}'
            else:
                ccell = editor.selection.current_cursor_cell
                ccell_name = editor.display.get_cell_name_from_position(ccell.column, ccell.row)
                label = f'{editor.selection.current_cell_name}:{ccell_name}'

            if n_selected > 1:
                label += f' ({format_string('%d', n_selected, grouping = True)} {_('cells')})'
            self.SceneSelections.set_label(label)

            label = f'{_('Tables')}: {format_string('%d', len(editor.document.tables), grouping = True)}'
            self.SceneStatistics.set_label(label)
