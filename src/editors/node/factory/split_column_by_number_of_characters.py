# split_column_by_number_of_characters.py
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

import logging

from ._template import NodeTemplate
from ._utils import isdatatable
from ._utils import take_snapshot

from ..content import NodeContent
from ..frame import NodeFrame
from ..socket import NodeSocket
from ..socket import NodeSocketType
from ..widgets import NodeComboButton
from ..widgets import NodeLabel
from ..widgets import NodeSpinButton

logger = logging.getLogger(__name__)

class NodeSplitColumnByNumberOfCharacters(NodeTemplate):

    ndname = _('Split Column by Number of Characters')

    action = 'split-column-by-number-of-characters'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeSplitColumnByNumberOfCharacters(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns']    = []
        self.frame.data['column']     = ''
        self.frame.data['n-chars']    = 0
        self.frame.data['strategies'] = {'first':  _('First'),
                                         'last':   _('Last'),
                                         'repeat': _('Repeat')}
        self.frame.data['strategy']   = 'first'

        self._add_output()
        self._add_input()
        self._add_column()
        self._add_n_chars()
        self._add_strategy()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column']   = args[0]
        self.frame.data['n-chars']  = args[1]
        self.frame.data['strategy'] = args[2]

        widget = self.frame.contents[3].Widget
        widget.set_data(args[1])

        options = self.frame.data['strategies']
        option = option = next(k for k in options.keys())
        if args[2] in options:
            option = options[args[2]]
        widget = self.frame.contents[4].Widget
        widget.set_data(option)

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
            from polars import struct

            column   = self.frame.data['column']
            n_chars  = self.frame.data['n-chars']
            strategy = self.frame.data['strategy']

            n_columns = 0

            expr = col(column)

            table = table.lazy()

            dtype = table.collect_schema()[column]
            if not isinstance(dtype, String):
                expr = expr.cast(String)

            match strategy:
                case 'first':
                    expr = struct([
                        expr.str.slice(0, n_chars).alias(f'{column}_0'),
                        expr.str.slice(n_chars).alias(f'{column}_1'),
                    ])
                    n_columns = 2

                case 'last':
                    expr = expr.str.len_chars() - n_chars
                    expr = struct([
                        expr.str.slice(0, expr).alias(f'{column}_0'),
                        expr.str.slice(-n_chars).alias(f'{column}_1'),
                    ])
                    n_columns = 2

                case 'repeat':
                    ncol_expr = expr.str.len_chars().max() / n_chars
                    n_columns = int(table.select(ncol_expr).collect().item())
                    expr = expr.str.extract_all(f'.{{1,{n_chars}}}') \
                               .list.to_struct(upper_bound = n_columns)

            names = [f'{column}_{i}' for i in range(n_columns)]
            expr = expr.struct.rename_fields(names)
            table = table.with_columns(expr.alias(column)).unnest(column)

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'column':   self.frame.data['column'],
            'n-chars':  self.frame.data['n-chars'],
            'strategy': self.frame.data['strategy'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['column'],
                          value['n-chars'],
                          value['strategy'])
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

    def _add_n_chars(self) -> None:
        """"""
        def get_data() -> int:
            """"""
            return self.frame.data['n-chars']

        def set_data(value: int) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                self.frame.data['n-chars'] = value
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        widget = NodeSpinButton(title    = _('No. Characters'),
                                get_data = get_data,
                                set_data = set_data,
                                lower    = 1,
                                digits   = 0)
        self.frame.add_content(widget   = widget,
                               get_data = get_data,
                               set_data = set_data)

    def _add_strategy(self) -> None:
        """"""
        def get_data() -> str:
            """"""
            return self.frame.data['strategy']

        def set_data(value: str) -> None:
            """"""
            def callback(value: str) -> None:
                """"""
                self.frame.data['strategy'] = value
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        widget = NodeComboButton(title    = _('Strategy'),
                                 get_data = get_data,
                                 set_data = set_data,
                                 options  = self.frame.data['strategies'])
        self.frame.add_content(widget   = widget,
                               get_data = get_data,
                               set_data = set_data)