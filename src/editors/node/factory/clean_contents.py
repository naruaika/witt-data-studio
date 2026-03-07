# clean_contents.py
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
from ..widgets import NodeCheckButton
from ..widgets import NodeLabel

logger = logging.getLogger(__name__)

class NodeCleanContents(NodeTemplate):

    ndname = _('Clean Contents')

    action = 'clean-contents'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCleanContents(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns']  = []
        self.frame.data['column']   = ''
        self.frame.data['to-keeps'] = []

        self._add_output()
        self._add_input()
        self._add_column()
        self._add_to_keeps_group()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column']   = args[0]
        self.frame.data['to-keeps'] = args[1]

        widget = self.frame.contents[3].Widget
        widget = widget.get_child()
        widget = widget.get_first_child()
        widget.set_data(0 in args[1])
        widget = widget.get_next_sibling()
        widget.set_data(1 in args[1])

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
            column = self.frame.data['column']
            to_keeps = self.frame.data['to-keeps']
            keep_newline = 0 in to_keeps
            keep_tab = 1 in to_keeps
            pattern = self._get_regex_pattern(keep_newline, keep_tab)
            table = table.with_columns(col(column).str.replace_all(pattern, ''))

        self.frame.data['table'] = table

    def _get_regex_pattern(self,
                           keep_newline: bool = False,
                           keep_tab:     bool = False,
                           ) ->          str:
        """"""
        excluded = set()

        if keep_newline:
            excluded.add(0x0A) # \n
        if keep_tab:
            excluded.add(0x09) # \t

        ranges = []

        def add_range(start: int,
                      end:   int,
                      ) ->   None:
            """"""
            chars = [i for i in range(start, end + 1) if i not in excluded]
            if chars:
                ranges.append(''.join(f'\\x{i:02X}' for i in chars))

        add_range(0x00, 0x1F)
        add_range(0x7F, 0x9F)

        return f'[{''.join(ranges)}]'

    def do_save(self) -> dict:
        """"""
        return {
            'column':   self.frame.data['column'],
            'to-keeps': self.frame.data['to-keeps'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['column'],
                          value['to-keeps'])
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

        import polars.selectors as cs
        table_columns = table.select(cs.string()) \
                             .collect_schema() \
                             .names()

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

    def _add_to_keeps_group(self) -> None:
        """"""
        box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        box.add_css_class('linked')

        box.append(self._add_newlines())
        box.append(self._add_tabs())

        expander = Gtk.Expander(label = _('To Keep'),
                                child = box)
        self.frame.add_content(expander)

    def _add_newlines(self) -> None:
        """"""
        def get_data() -> bool:
            """"""
            return 0 in self.frame.data['to-keeps']

        def set_data(value: bool) -> None:
            """"""
            def callback(value: bool) -> None:
                """"""
                if value and 0 not in self.frame.data['to-keeps']:
                    self.frame.data['to-keeps'].append(0)
                if not value and 0 in self.frame.data['to-keeps']:
                    self.frame.data['to-keeps'].remove(0)
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        check = NodeCheckButton(title    = _('Newlines'),
                                get_data = get_data,
                                set_data = set_data)

        return check

    def _add_tabs(self) -> None:
        """"""
        def get_data() -> bool:
            """"""
            return 1 in self.frame.data['to-keeps']

        def set_data(value: bool) -> None:
            """"""
            def callback(value: bool) -> None:
                """"""
                if value and 1 not in self.frame.data['to-keeps']:
                    self.frame.data['to-keeps'].append(1)
                if not value and 1 in self.frame.data['to-keeps']:
                    self.frame.data['to-keeps'].remove(1)
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        check = NodeCheckButton(title    = _('Tabs'),
                                get_data = get_data,
                                set_data = set_data)

        return check