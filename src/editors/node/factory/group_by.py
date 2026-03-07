# group_by.py
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
from ..widgets import NodeListEntry

logger = logging.getLogger(__name__)

class NodeGroupBy(NodeTemplate):

    ndname = _('Group By')

    action = 'group-by'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeGroupBy(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['all-columns']        = []
        self.frame.data['groupings']          = []
        self.frame.data['all-aggregations']   = {'count':       _('Count'),
                                                 'sum':         _('Summation'),
                                                 'median':      _('Median'),
                                                 'mean':        _('Average'),
                                                 'max':         _('Maximum'),
                                                 'min':         _('Minimum'),
                                                 'std':         _('Std. Deviation'),
                                                 'var':         _('Variance'),
                                                 'quantile:1':  _('1st Quartile'),
                                                 'quantile:2':  _('2nd Quartile'),
                                                 'quantile:3':  _('3rd Quartile'),
                                                 'product':     _('Product'),
                                                 'first':       _('First'),
                                                 'last':        _('Last'),
                                                 'n_unique':    _('No. Unique'),
                                                 'null_count':  _('No. Blank'),
                                                 'implode':     _('Implode'),
                                                 'bitwise_and': _('Bitwise AND'),
                                                 'bitwise_or':  _('Bitwise OR'),
                                                 'bitwise_xor': _('Bitwise XOR')}
        self.frame.data['aggregations']       = []
        self.frame.data['refresh-selector']   = False
        self.frame.data['grouping.exp']       = False
        self.frame.data['aggregate.exp']      = False

        self._add_output()
        self._add_input()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['groupings']        = args[0]
        self.frame.data['aggregations']     = args[1]
        self.frame.data['refresh-selector'] = True
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
            if aggregations := self.frame.data['aggregations']:
                from polars import col
                by = self.frame.data['groupings']
                exprs = []
                for alias, agg_name, col_name in aggregations:
                    expr = col(col_name)
                    if agg_name.startswith('quantile'):
                        func_args, func_name = agg_name.split(':')
                        expr = getattr(expr, func_name, None)
                        expr = expr(int(func_args) * 0.25)
                    else:
                        expr = getattr(expr, agg_name, None)()
                    expr = expr.alias(alias or f'{agg_name}_{col_name}')
                    exprs.append(expr)
                if exprs:
                    table = table.group_by(by).agg(*exprs)

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'groupings':    deepcopy(self.frame.data['groupings']),
            'aggregations': deepcopy(self.frame.data['aggregations']),
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['groupings'],
                          value['aggregations'])
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

        # Filter unvalid selection
        if table_columns:
            if self.frame.data['groupings']:
                groupings = []
                for column in table_columns:
                    if column in self.frame.data['groupings']:
                        groupings.append(column)
                groupings = groupings or table_columns
                self.frame.data['groupings'] = groupings

            if self.frame.data['aggregations']:
                aggregations = []
                for aggregation in self.frame.data['aggregations']:
                    *_, column = aggregation
                    if column in table_columns:
                        aggregations.append(aggregation)
                self.frame.data['aggregations'] = aggregations

        if self.frame.data['all-columns'] != table_columns:
            self.frame.data['refresh-selector'] = True

        self.frame.data['all-columns'] = table_columns

        if self.frame.data['refresh-selector']:
            if len(self.frame.contents) == 4:
                content = self.frame.contents[-1]
                self.frame.remove_content(content)
                content = self.frame.contents[-1]
                self.frame.remove_content(content)
            if table_columns:
                self._add_selector()

        if len(self.frame.contents) == 4:
            if self.frame.data['grouping.exp']:
                widget = self.frame.contents[2].Widget
                widget.set_expanded(True)

            if self.frame.data['aggregate.exp']:
                widget = self.frame.contents[3].Widget
                widget.set_expanded(True)

        self.frame.data['refresh-selector'] = False

    def _add_selector(self) -> None:
        """"""
        def get_groupings() -> list[str]:
            """"""
            return self.frame.data['groupings']

        def set_groupings(value: list[str]) -> None:
            """"""
            def callback(value: list[str]) -> None:
                """"""
                self.frame.data['groupings'] = value
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        group = NodeCheckGroup(get_data = get_groupings,
                               set_data = set_groupings,
                               options  = self.frame.data['all-columns'])
        expander = Gtk.Expander(label = _('Grouping'),
                                child = group)
        self.frame.add_content(expander)

        def on_groupings_expanded(widget:     Gtk.Widget,
                                  param_spec: GObject.ParamSpec,
                                  ) ->        None:
            """"""
            self.frame.data['grouping.exp'] = expander.get_expanded()

        expander.connect('notify::expanded', on_groupings_expanded)

        def get_aggregations() -> list:
            """"""
            return self.frame.data['aggregations']

        def set_aggregations(value: list) -> None:
            """"""
            def callback(value: list) -> None:
                """"""
                self.frame.data['aggregations'] = value
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        contents = [
            (
                'dropdown',
                self.frame.data['all-aggregations'],
            ),
            (
                'dropdown',
                {c: c for c in self.frame.data['all-columns']},
            ),
        ]
        widget = NodeListEntry(title    = _('Aggregation'),
                               get_data = get_aggregations,
                               set_data = set_aggregations,
                               contents = contents)
        expander = Gtk.Expander(label = _('Aggregations'),
                                child = widget)
        self.frame.add_content(expander)

        def on_aggregations_expanded(widget:     Gtk.Widget,
                                     param_spec: GObject.ParamSpec,
                                     ) ->        None:
            """"""
            self.frame.data['aggregate.exp'] = expander.get_expanded()

        expander.connect('notify::expanded', on_aggregations_expanded)