# choose_columns.py
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
import logging

from ._template import NodeTemplate
from ._utils import isdatatable
from ._utils import take_snapshot

from ..content import NodeContent
from ..frame import NodeFrame
from ..socket import NodeSocket
from ..socket import NodeSocketType
from ..widgets import NodeCheckGroup
from ..widgets import NodeLabel

logger = logging.getLogger(__name__)

class NodeChooseColumns(NodeTemplate):

    ndname = _('Choose Columns')

    action = 'choose-columns'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeChooseColumns(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['all-columns']     = []
        self.frame.data['columns']         = []
        self.frame.data['refresh-columns'] = False
        self.frame.data['column.exp']      = False

        self._add_output()
        self._add_input()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['columns'] = args[0]
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

        table_columns = self.frame.data['all-columns']

        if table_columns:
            if columns := self.frame.data['columns']:
                sorted_columns = []
                for column in table_columns:
                    if column in columns:
                        sorted_columns.append(column)
                if sorted_columns:
                    table = table.select(sorted_columns)

        self.frame.data['table'] = table

    def do_save(self) -> list:
        """"""
        return deepcopy(self.frame.data['columns'])

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
            if len(self.frame.contents) == 3:
                content = self.frame.contents[-1]
                self.frame.remove_content(content)
            if table_columns:
                self._add_selector()

        if self.frame.data['column.exp']:
            if len(self.frame.contents) == 3:
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