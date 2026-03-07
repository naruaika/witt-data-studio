# split_column_by_delimiter.py
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
import logging

from ._template import NodeTemplate
from ._utils import isdatatable
from ._utils import take_snapshot

from ..content import NodeContent
from ..frame import NodeFrame
from ..socket import NodeSocket
from ..socket import NodeSocketType
from ..widgets import NodeComboButton
from ..widgets import NodeEntry
from ..widgets import NodeLabel
from ..widgets import NodeSpinButton

logger = logging.getLogger(__name__)

class NodeSplitColumnByDelimiter(NodeTemplate):

    ndname = _('Split Column by Delimiter')

    action = 'split-column-by-delimiter'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeSplitColumnByDelimiter(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns']      = []
        self.frame.data['column']       = ''
        self.frame.data['delimiter']    = ','
        self.frame.data['delimiters']   = {',':  _('Comma'),
                                           '=':  _('Equal Sign'),
                                           ';':  _('Semicolon'),
                                           ' ':  _('Space'),
                                           '\t': _('Tab'),
                                           '$':  _('Custom')}
        self.frame.data['ct.delimiter'] = False
        self.frame.data['n-columns']    = 0
        self.frame.data['split-ats']    = {'every': _('Every Occurrence'),
                                           'first': _('First Occurrence')}
        self.frame.data['split-at']     = 'every'

        self._add_output()
        self._add_input()
        self._add_column()
        self._add_delimiter()
        self._add_options()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column']    = args[0]
        self.frame.data['delimiter'] = args[1]
        self.frame.data['n-columns'] = args[2]
        self.frame.data['split-at']  = args[3]

        options = self.frame.data['delimiters']
        is_custom = args[1] not in options
        use_custom = self.frame.data['ct.delimiter']
        box = self.frame.contents[3].Widget
        combo = box.get_first_child()
        entry = combo.get_next_sibling()
        if is_custom and not use_custom:
            option = list(options.values())[-1]
            combo.set_data(option)
            entry.set_data(args[1])
            entry.set_visible(True)
            self.frame.data['ct.delimiter'] = True
        else:
            combo.set_data(options[args[1]])
            entry.set_visible(False)

        box = self.frame.contents[4].Widget
        spin = box.get_first_child()
        spin.set_data(args[2])

        options = self.frame.data['split-ats']
        option = option = next(k for k in options.keys())
        if args[3] in options:
            option = options[args[3]]
        combo = spin.get_next_sibling()
        combo.set_data(option)
        combo.set_sensitive(args[2] > 0)

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        from polars import DataFrame

        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        if not isdatatable(table):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            from polars import String

            column    = self.frame.data['column']
            delimiter = self.frame.data['delimiter']
            n_columns = self.frame.data['n-columns']
            split_at  = self.frame.data['split-at']

            expr = col(column)

            table = table.lazy()

            dtype = table.collect_schema()[column]
            if not isinstance(dtype, String):
                expr = expr.cast(String)

            if n_columns == 0:
                n_matches = expr.str.count_matches(delimiter, literal = True)
                n_columns = table.select((n_matches + 1).max()).collect().item()

            if split_at == 'first':
                expr = expr.str.splitn(delimiter, n_columns)
            else:
                expr = expr.str.split_exact(delimiter, n_columns - 1)

            names = [f'{column}_{i}' for i in range(n_columns)]
            expr = expr.struct.rename_fields(names)
            table = table.with_columns(expr).unnest(column)

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'column':    self.frame.data['column'],
            'delimiter': self.frame.data['delimiter'],
            'n-columns': self.frame.data['n-columns'],
            'split-at':  self.frame.data['split-at'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['column'],
                          value['delimiter'],
                          value['n-columns'],
                          value['split-at'])
        except Exception as e:
            logger.error(e, exc_info = True)
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

    def _add_output(self) -> None:
        """"""
        from polars import DataFrame

        self.frame.data['table'] = DataFrame()

        def get_data() -> DataFrame:
            """"""
            return self.frame.data['table']

        def set_data(value: DataFrame) -> None:
            """"""
            self.frame.data['table'] = value
            self.frame.do_execute(backward = False)

        widget = NodeLabel(_('Table'))
        socket_type = NodeSocketType.OUTPUT
        self.frame.add_content(widget      = widget,
                               socket_type = socket_type,
                               data_type   = DataFrame,
                               get_data    = get_data,
                               set_data    = set_data)

    def _add_input(self) -> None:
        """"""
        from polars import DataFrame

        label = NodeLabel(_('Table'), can_link = True)
        socket_type = NodeSocketType.INPUT
        self.frame.add_content(widget      = label,
                               socket_type = socket_type,
                               data_type   = DataFrame)

    def _refresh_column(self) -> None:
        """"""
        table = self.frame.data['table']

        table_columns = table.collect_schema().names()

        self.frame.data['columns'] = table_columns

        widget = self.frame.contents[2].Widget

        if not table_columns:
            widget.set_sensitive(False)
            return

        if self.frame.data['column'] not in table_columns:
            self.frame.data['column'] = table_columns[0]

        widget.set_options(self.frame.data['columns'])
        widget.set_data(self.frame.data['column'])
        widget.set_sensitive(True)

    def _add_column(self) -> None:
        """"""
        def get_data() -> str:
            """"""
            return self.frame.data['column']

        def set_data(value: str) -> None:
            """"""
            def callback(value: str) -> None:
                """"""
                self.frame.data['column'] = value
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)

    def _add_delimiter(self) -> None:
        """"""
        box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        box.add_css_class('linked')
        self.frame.add_content(box)

        def get_custom() -> str:
            """"""
            return self.frame.data['delimiter']

        def set_custom(value: str) -> None:
            """"""
            def callback(value: str) -> None:
                """"""
                self.frame.data['delimiter'] = value
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        entry = NodeEntry(title    = _('Custom'),
                          get_data = get_custom,
                          set_data = set_custom)
        entry.set_visible(False)

        def get_data() -> str:
            """"""
            if self.frame.data['ct.delimiter']:
                return '$'
            return self.frame.data['delimiter']

        def set_data(value: str) -> None:
            """"""
            def callback(value: str) -> None:
                """"""
                if value == '$':
                    value = entry.get_data()
                    self.frame.data['delimiter'] = value
                    self.frame.data['ct.delimiter'] = True
                    entry.set_visible(True)
                else:
                    self.frame.data['delimiter'] = value
                    self.frame.data['ct.delimiter'] = False
                    entry.set_visible(False)
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Delimiter'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['delimiters'])

        box.append(combo)
        box.append(entry)

    def _add_options(self) -> None:
        """"""
        box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        box.add_css_class('linked')
        self.frame.add_content(box)

        def get_split_at() -> str:
            """"""
            return self.frame.data['split-at']

        def set_split_at(value: str) -> None:
            """"""
            def callback(value: str) -> None:
                """"""
                self.frame.data['split-at'] = value
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('At Delimiter'),
                                get_data = get_split_at,
                                set_data = set_split_at,
                                options  = self.frame.data['split-ats'])

        def get_n_columns() -> int:
            """"""
            return self.frame.data['n-columns']

        def set_n_columns(value: int) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                combo.set_sensitive(value > 0)
                self.frame.data['n-columns'] = value
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        spin = NodeSpinButton(title    = _('No. Columns'),
                              get_data = get_n_columns,
                              set_data = set_n_columns,
                              lower    = 0,
                              digits   = 0)

        box.append(spin)
        box.append(combo)