# extract_text_after_delimiter.py
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
from ._utils    import iscompatible
from ._utils    import isdatatable
from ._utils    import take_snapshot

from ..content import NodeContent
from ..frame   import NodeFrame
from ..socket  import NodeSocket
from ..socket  import NodeSocketType
from ..widgets import NodeComboButton
from ..widgets import NodeEntry
from ..widgets import NodeLabel

logger = logging.getLogger(__name__)

class NodeExtractTextAfterDelimiter(NodeTemplate):

    ndname = _('Extract Text After Delimiter')

    action = 'extract-text-after-delimiter'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeExtractTextAfterDelimiter(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''
        self.frame.data['delimiter']  = ''

        self._add_output()
        self._add_input()
        self._add_column()
        self._add_delimiter()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.data['delimiter'] = args[1]

        widget = self.frame.contents[3].Widget
        widget.set_data(args[1])

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

            column = self.frame.data['column']
            delimiter = self.frame.data['delimiter']

            expr = col(column)

            dtype = table.collect_schema()[column]
            if not isinstance(dtype, String):
                expr = expr.cast(String)

            expr = expr.str.splitn(delimiter, 2) \
                       .struct.field('field_1').fill_null('')
            table = table.with_columns(expr.alias(column))

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'column': self.frame.data['column'],
            'delimiter': self.frame.data['delimiter'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['column'],
                          value['delimiter'])
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

    def _add_delimiter(self) -> None:
        """"""
        def get_data() -> str:
            """"""
            return self.frame.data['delimiter']

        def set_data(value: str) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                self.frame.data['delimiter'] = value
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        entry = NodeEntry(title    = _('Delimiter'),
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

            label = NodeLabel(_('Delimiter'), can_link = True)
            label.insert_after(content.Container, content.Socket)

            if not iscompatible(pair_socket, self_content):
                return

            self.frame.data['delimiter.bak'] = content.get_data()

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            if 'delimiter.bak' in self.frame.data:
                content.set_data(self.frame.data['delimiter.bak'])

            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink