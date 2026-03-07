# replace_values.py
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

from copy import deepcopy
from gi.repository import GObject
from gi.repository import Gtk
from polars import DataType
from polars import Expr
import logging

from ._template import NodeTemplate
from ._utils import iscompatible
from ._utils import isdatatable
from ._utils import take_snapshot

from ..content import NodeContent
from ..frame import NodeFrame
from ..socket import NodeSocket
from ..socket import NodeSocketType
from ..widgets import NodeCheckButton
from ..widgets import NodeCheckGroup
from ..widgets import NodeEntry
from ..widgets import NodeLabel

logger = logging.getLogger(__name__)

class NodeReplaceValues(NodeTemplate):

    ndname = _('Replace Values')

    action = 'replace-values'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeReplaceValues(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['search']          = ''
        self.frame.data['replace']         = ''
        self.frame.data['options']         = []
        self.frame.data['all-columns']     = []
        self.frame.data['columns']         = []
        self.frame.data['refresh-columns'] = False
        self.frame.data['option.exp']      = False
        self.frame.data['column.exp']      = False

        self._add_output()
        self._add_input()
        self._add_search()
        self._add_replace()
        self._add_options_group()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['search']  = args[0]
        self.frame.data['replace'] = args[1]
        self.frame.data['options'] = args[2]
        self.frame.data['columns'] = args[3]

        widget = self.frame.contents[2].Widget
        widget.set_data(args[0])

        widget = self.frame.contents[3].Widget
        widget.set_data(args[1])

        widget = self.frame.contents[4].Widget
        widget = widget.get_child()
        widget = widget.get_first_child()
        widget.set_data(0 in args[2])
        widget = widget.get_next_sibling()
        widget.set_data(1 in args[2])
        widget = widget.get_next_sibling()
        widget.set_data(2 in args[2])

        self.frame.data['refresh-columns'] = True
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
            self._refresh_selector()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        if not isdatatable(table):
            self.frame.data['table'] = DataFrame()
            self._refresh_selector()
            return

        self.frame.data['table'] = table
        self._refresh_selector()

        table_schema = table.collect_schema()
        table_columns = table_schema.names()

        self.frame.data['table'] = table

        if not table_columns:
            return

        columns = self.frame.data['columns']

        if not columns:
            columns = self.frame.data['all-columns']

        from polars import col
        from polars import String

        expressions = []

        for column in columns:
            expression = col(column)
            try:
                if table_schema[column] == String:
                    expression = self._replace_text(expression,
                                                    self.frame.data['search'],
                                                    self.frame.data['replace'],
                                                    self.frame.data['options'])
                else:
                    expression = self._replace_non_text(expression,
                                                        self.frame.data['search'],
                                                        self.frame.data['replace'],
                                                        table_schema[column])
            except:
                continue
            expression = expression.name.keep()
            expressions.append(expression)

        self.frame.data['table'] = table.with_columns(expressions)

    def _replace_text(self,
                      expr:    Expr,
                      search:  str,
                      replace: str,
                      options: list,
                      ) ->     Expr:
        """"""
        from polars import when

        search = str(search) or None
        replace = str(replace)

        if not search:
            then_expr = expr.fill_null(replace)
            return when(expr.is_null()).then(then_expr).otherwise(expr)

        match_cell = 0 in options
        match_case = 1 in options
        use_regexp = 2 in options

        when_expr = expr.str.contains_any([search], ascii_case_insensitive = not match_case)
        if match_cell:
            when_expr = expr.str.to_lowercase() == search.lower()
            if match_case:
                when_expr = expr.str == search
        if use_regexp:
            when_expr = expr.str.contains(f'(?i){search}')
            if match_case:
                when_expr = expr.str.contains(search)

        if not use_regexp:
            from re import escape
            search = escape(search)
        if not match_case:
            search = f'(?i){search}'

        then_expr = expr.str.replace_all(search, replace)

        return when(when_expr).then(then_expr).otherwise(expr)

    def _replace_non_text(self,
                          expr:    Expr,
                          search:  str,
                          replace: str,
                          dtype:   DataType,
                          ) ->     Expr:
        """"""
        from polars import Datetime
        from polars import Date
        from polars import Time

        if dtype == Datetime:
            from ....core.utils import todatetime
            search = todatetime(search)
            replace = todatetime(replace)

        if dtype == Date:
            from ....core.utils import todate
            search = todate(search)
            replace = todate(replace)

        if dtype == Time:
            from ....core.utils import totime
            search = totime(search)
            replace = totime(replace)

        if dtype not in {Datetime, Date, Time}:
            from polars import Series
            search = Series([search]).cast(dtype).item()
            replace = Series([replace]).cast(dtype).item()

        return expr.replace(search, replace)

    def do_save(self) -> dict:
        """"""
        return {
            'search':  self.frame.data['search'],
            'replace': self.frame.data['replace'],
            'options': deepcopy(self.frame.data['options']),
            'columns': deepcopy(self.frame.data['columns']),
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['search'],
                          value['replace'],
                          value['options'],
                          value['columns'])
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

    def _add_search(self) -> None:
        """"""
        def get_data() -> str:
            """"""
            return self.frame.data['search']

        def set_data(value: str) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                self.frame.data['search'] = value
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        entry = NodeEntry(title    = _('Search'),
                          get_data = get_data,
                          set_data = set_data)
        socket_type = NodeSocketType.INPUT
        content = self.frame.add_content(widget      = entry,
                                         socket_type = socket_type,
                                         data_type   = str,
                                         get_data    = get_data,
                                         set_data    = set_data)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            content.Widget.set_visible(False)

            label = NodeLabel(_('Search'), can_link = True)
            label.insert_after(content.Container, content.Socket)

            if not iscompatible(pair_socket, self_content):
                return

            self.frame.data['search.bak'] = content.get_data()

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            if 'search.bak' in self.frame.data:
                content.set_data(self.frame.data['search.bak'])

            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink

    def _add_replace(self) -> None:
        """"""
        def get_data() -> str:
            """"""
            return self.frame.data['replace']

        def set_data(value: str) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                self.frame.data['replace'] = value
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        entry = NodeEntry(title    = _('Replace'),
                          get_data = get_data,
                          set_data = set_data)
        socket_type = NodeSocketType.INPUT
        content = self.frame.add_content(widget      = entry,
                                         socket_type = socket_type,
                                         data_type   = str,
                                         get_data    = get_data,
                                         set_data    = set_data)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            content.Widget.set_visible(False)

            label = NodeLabel(_('Replace'), can_link = True)
            label.insert_after(content.Container, content.Socket)

            if not iscompatible(pair_socket, self_content):
                return

            self.frame.data['replace.bak'] = content.get_data()

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            if 'replace.bak' in self.frame.data:
                content.set_data(self.frame.data['replace.bak'])

            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink

    def _add_options_group(self) -> None:
        """"""
        box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        box.add_css_class('linked')

        box.append(self._add_exact_match())
        box.append(self._add_case_sensitive())
        box.append(self._add_regular_expression())

        expander = Gtk.Expander(label = _('Search Options'),
                                child = box)
        self.frame.add_content(expander)

    def _add_exact_match(self) -> None:
        """"""
        def get_data() -> bool:
            """"""
            return 0 in self.frame.data['options']

        def set_data(value: bool) -> None:
            """"""
            def callback(value: bool) -> None:
                """"""
                if value and 0 not in self.frame.data['options']:
                    self.frame.data['options'].append(0)
                if not value and 0 in self.frame.data['options']:
                    self.frame.data['options'].remove(0)
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        check = NodeCheckButton(title    = _('Exact Match'),
                                get_data = get_data,
                                set_data = set_data)

        return check

    def _add_case_sensitive(self) -> None:
        """"""
        def get_data() -> bool:
            """"""
            return 1 in self.frame.data['options']

        def set_data(value: bool) -> None:
            """"""
            def callback(value: bool) -> None:
                """"""
                if value and 1 not in self.frame.data['options']:
                    self.frame.data['options'].append(1)
                if not value and 1 in self.frame.data['options']:
                    self.frame.data['options'].remove(1)
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        check = NodeCheckButton(title    = _('Case Sensitive'),
                                get_data = get_data,
                                set_data = set_data)

        return check

    def _add_regular_expression(self) -> None:
        """"""
        def get_data() -> bool:
            """"""
            return 2 in self.frame.data['options']

        def set_data(value: bool) -> None:
            """"""
            def callback(value: bool) -> None:
                """"""
                if value and 2 not in self.frame.data['options']:
                    self.frame.data['options'].append(2)
                if not value and 2 in self.frame.data['options']:
                    self.frame.data['options'].remove(2)
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        check = NodeCheckButton(title    = _('Regular Expression'),
                                get_data = get_data,
                                set_data = set_data)

        return check

    def _refresh_selector(self) -> None:
        """"""
        table = self.frame.data['table']

        table_columns = table.collect_schema().names()

        # Filter unvalid columns from selection
        if table_columns:
            if self.frame.data['columns']:
                columns = []
                for column in table_columns:
                    if column in self.frame.data['columns']:
                        columns.append(column)
                columns = columns or table_columns
                self.frame.data['columns'] = columns

        if self.frame.data['all-columns'] != table_columns:
            self.frame.data['refresh-columns'] = True

        self.frame.data['all-columns'] = table_columns

        if self.frame.data['refresh-columns']:
            if len(self.frame.contents) == 6:
                content = self.frame.contents[-1]
                self.frame.remove_content(content)
            if table_columns:
                self._add_selector()

        if self.frame.data['column.exp']:
            if len(self.frame.contents) == 6:
                widget = self.frame.contents[-1].Widget
                widget.set_expanded(True)

        self.frame.data['refresh-columns'] = False

    def _add_selector(self) -> None:
        """"""
        def get_data() -> list[str]:
            """"""
            return self.frame.data['columns']

        def set_data(value: list[str]) -> None:
            """"""
            def callback(value: list[str]) -> None:
                """"""
                self.frame.data['columns'] = value
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        group = NodeCheckGroup(get_data = get_data,
                               set_data = set_data,
                               options  = self.frame.data['all-columns'])
        expander = Gtk.Expander(label = _('Search On'),
                                child = group)
        self.frame.add_content(expander)

        def on_expanded(widget:     Gtk.Widget,
                        param_spec: GObject.ParamSpec,
                        ) ->        None:
            """"""
            self.frame.data['column.exp'] = expander.get_expanded()

        expander.connect('notify::expanded', on_expanded)