# sort_rows.py
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

from copy          import deepcopy
from gi.repository import GObject
from gi.repository import Gtk

import logging

from ._template import NodeTemplate
from ._utils    import isdatatable
from ._utils    import take_snapshot

from ..content import NodeContent
from ..frame   import NodeFrame
from ..socket  import NodeSocket
from ..socket  import NodeSocketType
from ..widgets import NodeLabel
from ..widgets import NodeListItem

logger = logging.getLogger(__name__)

class NodeSortRows(NodeTemplate):

    ndname = _('Sort Rows')

    action = 'sort-rows'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeSortRows(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['all-columns']    = []
        self.frame.data['levels']         = []
        self.frame.data['refresh-levels'] = True
        self.frame.data['level.exp']      = False

        self._add_output()
        self._add_input()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['levels'] = args[0]
        self.frame.data['refresh-levels'] = True
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
            if levels := self.frame.data['levels']:
                bys = []
                descending = []
                for by, order in levels:
                    bys.append(by)
                    descending.append(order == 'descending')
                table = table.sort(by = bys, descending = descending)

        self.frame.data['table'] = table

    def do_save(self) -> list:
        """"""
        return deepcopy(self.frame.data['levels'])

    def do_restore(self,
                   value: list,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
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

    def _refresh_selector(self) -> None:
        """"""
        table = self.frame.data['table']

        table_columns = table.collect_schema().names()

        # Filter unvalid levels from selection
        if table_columns:
            if self.frame.data['levels']:
                levels = []
                for level in self.frame.data['levels']:
                    column, _ = level
                    if column in table_columns:
                        levels.append(level)
                self.frame.data['levels'] = levels

        if self.frame.data['all-columns'] != table_columns:
            self.frame.data['refresh-levels'] = True

        self.frame.data['all-columns'] = table_columns

        if self.frame.data['refresh-levels']:
            if len(self.frame.contents) == 3:
                content = self.frame.contents[-1]
                self.frame.remove_content(content)
            if table_columns:
                self._add_selector()

        if not self.frame.data['levels']:
            self.frame.data['level.exp'] = True

        if self.frame.data['level.exp']:
            if len(self.frame.contents) == 3:
                widget = self.frame.contents[-1].Widget
                widget.set_expanded(True)

        self.frame.data['refresh-levels'] = False

    def _add_selector(self) -> None:
        """"""
        def get_data() -> list:
            """"""
            return self.frame.data['levels']

        def set_data(value: list) -> None:
            """"""
            def callback(value: list) -> None:
                """"""
                self.frame.data['levels'] = value
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        contents = [
            (
                'dropdown',
                {c: c for c in self.frame.data['all-columns']},
            ),
            (
                'dropdown',
                {
                    'ascending':  _('Ascending'),
                    'descending': _('Descending'),
                },
            ),
        ]
        widget = NodeListItem(title    = _('Level'),
                              get_data = get_data,
                              set_data = set_data,
                              contents = contents)
        expander = Gtk.Expander(label = _('Levels'),
                                child = widget)
        self.frame.add_content(expander)

        def on_expanded(widget:     Gtk.Widget,
                        param_spec: GObject.ParamSpec,
                        ) ->        None:
            """"""
            self.frame.data['level.exp'] = widget.get_expanded()

        expander.connect('notify::expanded', on_expanded)