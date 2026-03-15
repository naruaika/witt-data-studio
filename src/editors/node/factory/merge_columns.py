# merge_columns.py
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

from gi.repository import GObject
from gi.repository import Gtk
import logging

from ._template import NodeTemplate
from ._utils import isdatatable
from ._utils import take_snapshot

from ..content import NodeContent
from ..frame import NodeFrame
from ..socket import NodeSocket
from ..socket import NodeSocketType
from ..widgets import NodeCheckGroup
from ..widgets import NodeComboButton
from ..widgets import NodeEntry
from ..widgets import NodeLabel

logger = logging.getLogger(__name__)

class NodeMergeColumns(NodeTemplate):

    ndname = _('Merge Columns')

    action = 'merge-columns'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeMergeColumns(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['all-columns']     = []
        self.frame.data['columns']         = []
        self.frame.data['separator']       = ''
        self.frame.data['separators']      = {'':   _('None'),
                                              ':':  _('Colon'),
                                              ',':  _('Comma'),
                                              '=':  _('Equal Sign'),
                                              ';':  _('Semicolon'),
                                              ' ':  _('Space'),
                                              '\t': _('Tab'),
                                              '$':  _('Custom')}
        self.frame.data['separator.ct']    = False
        self.frame.data['alias']           = ''
        self.frame.data['refresh-columns'] = False
        self.frame.data['column.exp']      = False

        self._add_output()
        self._add_input()
        self._add_separator()
        self._add_alias()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['columns']   = args[0]
        self.frame.data['separator'] = args[1]
        self.frame.data['alias']     = args[2]

        options = self.frame.data['separators']
        is_custom = args[1] not in options
        use_custom = self.frame.data['separator.ct']
        box = self.frame.contents[2].Widget
        combo = box.get_first_child()
        entry = combo.get_next_sibling()
        if is_custom and not use_custom:
            option = list(options.values())[-1]
            combo.set_data(option)
            entry.set_data(args[1])
            entry.set_visible(True)
            self.frame.data['separator.ct'] = True
        else:
            combo.set_data(options[args[1]])
            entry.set_visible(False)

        widget = self.frame.contents[3].Widget
        widget.set_data(args[2])

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

        if self.frame.data['all-columns']:
            from polars import col
            from polars import concat_str

            columns   = self.frame.data['columns']
            separator = self.frame.data['separator']
            alias     = self.frame.data['alias'] or columns[0]

            exprs = [col(column).fill_null('') for column in columns]
            expr = concat_str(exprs        = exprs,
                              separator    = separator,
                              ignore_nulls = True)

            table = table.with_columns(expr.alias(columns[0])) \
                         .drop(set(columns[1:]) - {alias}) \
                         .rename({columns[0]: alias})

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'columns':   self.frame.data['columns'],
            'separator': self.frame.data['separator'],
            'alias':     self.frame.data['alias'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['columns'],
                          value['separator'],
                          value['alias'])
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

    def _add_separator(self) -> None:
        """"""
        box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        box.add_css_class('linked')
        self.frame.add_content(box)

        def get_custom() -> str:
            """"""
            return self.frame.data['separator']

        def set_custom(value: str) -> None:
            """"""
            def callback(value: str) -> None:
                """"""
                self.frame.data['separator'] = value
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        entry = NodeEntry(title    = _('Custom'),
                          get_data = get_custom,
                          set_data = set_custom)
        entry.set_visible(False)

        def get_data() -> str:
            """"""
            if self.frame.data['separator.ct']:
                return '$'
            return self.frame.data['separator']

        def set_data(value: str) -> None:
            """"""
            def callback(value: str) -> None:
                """"""
                if value == '$':
                    value = entry.get_data()
                    self.frame.data['separator'] = value
                    self.frame.data['separator.ct'] = True
                    entry.set_visible(True)
                else:
                    self.frame.data['separator'] = value
                    self.frame.data['separator.ct'] = False
                    entry.set_visible(False)
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Separator'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['separators'])

        box.append(combo)
        box.append(entry)

    def _add_alias(self) -> None:
        """"""
        widget = None

        def get_data() -> str:
            """"""
            return self.frame.data['alias']

        def set_data(value: str) -> None:
            """"""
            def callback(value: str) -> None:
                """"""
                self.frame.data['alias'] = value
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        widget = NodeEntry(title    = _('Alias') + '?',
                           get_data = get_data,
                           set_data = set_data)
        self.frame.add_content(widget   = widget,
                               get_data = get_data,
                               set_data = set_data)

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
                self.frame.data['columns'] = columns

        if self.frame.data['all-columns'] != table_columns:
            self.frame.data['refresh-columns'] = True

        self.frame.data['all-columns'] = table_columns

        if self.frame.data['refresh-columns']:
            if len(self.frame.contents) == 5:
                content = self.frame.contents[-1]
                self.frame.remove_content(content)
            if table_columns:
                self._add_selector()

        if self.frame.data['column.exp']:
            if len(self.frame.contents) == 5:
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
        expander = Gtk.Expander(label = _('Columns'),
                                child = group)
        self.frame.add_content(expander)

        def on_expanded(widget:     Gtk.Widget,
                        param_spec: GObject.ParamSpec,
                        ) ->        None:
            """"""
            self.frame.data['column.exp'] = widget.get_expanded()

        expander.connect('notify::expanded', on_expanded)