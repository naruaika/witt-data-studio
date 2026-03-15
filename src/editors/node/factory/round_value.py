# round_value.py
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

class NodeRoundValue(NodeTemplate):

    ndname = _('Round Value')

    action = 'round-value'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeRoundValue(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns']  = []
        self.frame.data['column']   = ''
        self.frame.data['decimals'] = 1
        self.frame.data['modes'] = {'bankers':    _('Banker\'s'),
                                    'commercial': _('Commercial')}
        self.frame.data['mode']  = 'bankers'

        self._add_output()
        self._add_input()
        self._add_column()
        self._add_decimals()
        self._add_mode()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column']   = args[0]
        self.frame.data['decimals'] = args[1]
        self.frame.data['mode']     = args[2]

        widget = self.frame.contents[3].Widget
        widget.set_data(args[1])

        options = self.frame.data['modes']
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

            column = self.frame.data['column']
            decimals = self.frame.data['decimals']
            mode = self.frame.data['mode']

            if mode == 'bankers':
                mode = 'half_to_even'
            else:
                mode = 'half_away_from_zero'

            table = table.with_columns(col(column).round(decimals, mode))

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'column':   self.frame.data['column'],
            'decimals': self.frame.data['decimals'],
            'mode':     self.frame.data['mode'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['column'],
                          value['decimals'],
                          value['mode'])
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
        table_columns = table.select(cs.numeric()) \
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

    def _add_decimals(self) -> None:
        """"""
        def get_data() -> int:
            """"""
            return self.frame.data['decimals']

        def set_data(value: int) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                self.frame.data['decimals'] = value
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        widget = NodeSpinButton(title    = _('Decimals'),
                                get_data = get_data,
                                set_data = set_data,
                                lower    = 1,
                                digits   = 0)
        self.frame.add_content(widget   = widget,
                               get_data = get_data,
                               set_data = set_data)

    def _add_mode(self) -> None:
        """"""
        def get_data() -> str:
            """"""
            return self.frame.data['mode']

        def set_data(value: str) -> None:
            """"""
            def callback(value: str) -> None:
                """"""
                self.frame.data['mode'] = value
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        widget = NodeComboButton(title    = _('Mode'),
                                 get_data = get_data,
                                 set_data = set_data,
                                 options  = self.frame.data['modes'])
        self.frame.add_content(widget   = widget,
                               get_data = get_data,
                               set_data = set_data)