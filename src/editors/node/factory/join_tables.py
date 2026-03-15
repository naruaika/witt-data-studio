# join_tables.py
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
from ._utils    import iscompatible
from ._utils    import isdatatable
from ._utils    import take_snapshot

from ..content import NodeContent
from ..frame   import NodeFrame
from ..socket  import NodeSocket
from ..socket  import NodeSocketType
from ..widgets import NodeCheckGroup
from ..widgets import NodeComboButton
from ..widgets import NodeLabel

logger = logging.getLogger(__name__)

class NodeJoinTables(NodeTemplate):

    ndname = _('Join Tables')

    action = 'join-tables'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeJoinTables(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['ltable']      = None
        self.frame.data['ltname']      = ''
        self.frame.data['lcolumn']     = ''
        self.frame.data['lcolumns']    = []
        self.frame.data['lcolumn.exp'] = False

        self.frame.data['rtable']      = None
        self.frame.data['rtname']      = ''
        self.frame.data['rcolumn']     = ''
        self.frame.data['rcolumns']    = []
        self.frame.data['rcolumn.exp'] = False

        self.frame.data['strategies']  = {'inner': _('Inner'),
                                          'left':  _('Left'),
                                          'right': _('Right'),
                                          'full':  _('Full'),
                                          'cross': _('Cross'),
                                          'semi':  _('Semi'),
                                          'anti':  _('Anti')}
        self.frame.data['strategy']    = 'inner'

        self.frame.data['keep-orders'] = {'none':       _('None'),
                                          'left':       _('Left'),
                                          'right':      _('Right'),
                                          'left_right': _('Left-Right'),
                                          'right_left': _('Right-Left')}
        self.frame.data['keep-order']  = 'none'

        self._add_output()
        self._add_strategy()
        self._add_keep_order()
        self._add_input('left')
        self._add_input('right')

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['ltname']     = args[0]
        self.frame.data['lcolumn']    = args[1]
        self.frame.data['lcolumns']   = args[2]
        self.frame.data['rtname']     = args[3]
        self.frame.data['rcolumn']    = args[4]
        self.frame.data['rcolumns']   = args[5]
        self.frame.data['strategy']   = args[6]
        self.frame.data['keep-order'] = args[7]

        options = self.frame.data['strategies']
        option = next(k for k in options.keys())
        if args[6] in options:
            option = options[args[6]]
        widget = self.frame.contents[1].Widget
        widget.set_data(option)

        options = self.frame.data['keep-orders']
        option = next(k for k in options.keys())
        if args[7] in options:
            option = options[args[7]]
        widget = self.frame.contents[2].Widget
        widget.set_data(option)

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        from polars import DataFrame

        self_content = self.frame.contents[3]
        if not self_content.Socket.links:
            self.frame.data['table'] = DataFrame()
            return

        self_content = self.frame.contents[4]
        if not self_content.Socket.links:
            self.frame.data['table'] = DataFrame()
            return

        self._refresh_selectors()

        if (
            self.frame.data['ltable'] is None or
            self.frame.data['rtable'] is None or
            self.frame.data['lcolumn'] == ''  or
            self.frame.data['rcolumn'] == ''
        ):
            self.frame.data['table'] = DataFrame()
            return

        ltable   = self.frame.data['ltable']
        lcolumn  = self.frame.data['lcolumn']
        lcolumns = self.frame.data['lcolumns']
        rtable   = self.frame.data['rtable']
        rcolumn  = self.frame.data['rcolumn']
        rcolumns = self.frame.data['rcolumns']
        how      = self.frame.data['strategy']
        order    = self.frame.data['keep-order']

        ltable = ltable.select([lcolumn] + lcolumns)
        rtable = rtable.select([rcolumn] + rcolumns)

        table = ltable.join(other          = rtable,
                            left_on        = lcolumn,
                            right_on       = rcolumn,
                            how            = how,
                            maintain_order = order)

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'ltname':     self.frame.data['ltname'],
            'lcolumn':    self.frame.data['lcolumn'],
            'lcolumns':   self.frame.data['lcolumns'],
            'rtname':     self.frame.data['rtname'],
            'rcolumn':    self.frame.data['rcolumn'],
            'rcolumns':   self.frame.data['rcolumns'],
            'strategy':   self.frame.data['strategy'],
            'keep-order': self.frame.data['keep-order'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['ltname'],
                          value['lcolumn'],
                          value['lcolumns'],
                          value['rtname'],
                          value['rcolumn'],
                          value['rcolumns'],
                          value['strategy'],
                          value['keep-order'])
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

        combo = NodeComboButton(title    = _('Strategy'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['strategies'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

    def _add_keep_order(self) -> None:
        """"""
        def get_data() -> str:
            """"""
            return self.frame.data['keep-order']

        def set_data(value: str) -> None:
            """"""
            def callback(value: str) -> None:
                """"""
                self.frame.data['keep-order'] = value
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Maintain Order'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['keep-orders'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

    def _add_input(self,
                   prefix: str,
                   ) ->    None:
        """"""
        from polars import DataFrame
        from ....core.construct import Sheet

        container = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)

        label = NodeLabel(_('Left') if prefix == 'left' else _('Right'))
        label.set_xalign(0.0)
        container.append(label)

        expander = Gtk.Expander(label   = label.get_label(),
                                visible = False)
        container.append(expander)

        socket_type = NodeSocketType.INPUT
        content = self.frame.add_content(widget      = container,
                                         socket_type = socket_type,
                                         data_type   = (DataFrame, Sheet),
                                         auto_update = True)

        def restore_widget() -> None:
            """"""
            expander.set_child(None)
            expander.set_visible(False)

            label.set_visible(True)

            self.frame.data[f'{prefix}table']   = None
            self.frame.data[f'{prefix}tname']   = ''
            self.frame.data[f'{prefix}column']  = ''
            self.frame.data[f'{prefix}columns'] = []

        def replace_widget(pair_socket: NodeSocket) -> None:
            """"""
            restore_widget()

            box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL,
                          spacing     = 5)

            subbox = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
            subbox.add_css_class('linked')
            box.append(subbox)

            expander.set_child(box)
            expander.set_visible(True)

            label.set_visible(False)

            # Create table selector widget
            if pair_socket.data_type == Sheet:
                sheet = pair_socket.Content.get_data()
                tables = list(sheet.tables.keys())
                self._add_table_combo(prefix    = prefix,
                                      tables    = tables,
                                      content   = pair_socket.Content,
                                      container = subbox)

            # Create column selector widget
            else:
                table = pair_socket.Content.get_data()
                columns = []
                if isdatatable(table):
                    columns = table.collect_schema().names()
                    self.frame.data[f'{prefix}table'] = table
                self._add_column_combo(prefix    = prefix,
                                       columns   = columns,
                                       container = subbox)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            if not iscompatible(pair_socket, self_content):
                return

            replace_widget(pair_socket)

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_update(socket: NodeSocket) -> None:
            """"""
            restore_widget()

            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_update = do_update

    def _refresh_selectors(self) -> None:
        """"""
        self_content = self.frame.contents[3]
        links = self_content.Socket.links
        pair_socket = links[0].in_socket
        self._refresh_selector('left', pair_socket, self_content)

        self_content = self.frame.contents[4]
        links = self_content.Socket.links
        pair_socket = links[0].in_socket
        self._refresh_selector('right', pair_socket, self_content)

    def _refresh_selector(self,
                          prefix:       str,
                          pair_socket:  NodeSocket,
                          self_content: NodeContent,
                          ) ->          None:
        """"""
        from ....core.construct import Sheet

        busy = self.frame.is_processing
        self.frame.is_processing = True

        prefix = prefix[0]

        container = self_content.Widget
        expander = container.get_last_child()
        box = expander.get_child()
        subbox = box.get_first_child()

        # Update table selector widget
        if pair_socket.data_type == Sheet:
            sheet = pair_socket.Content.get_data()
            tables = list(sheet.tables.keys())
            table_combo = subbox.get_first_child()

            if tables != list(table_combo.options.keys()):
                table_combo.set_options(tables)
                table_combo._set_data(table_combo._get_data())

            else:
                tname = table_combo._get_data()
                table = sheet.tables[tname][1]
                columns = table.collect_schema().names()
                columns_combo = subbox.get_last_child()

                if columns != list(columns_combo.options.keys()):
                    columns_combo.set_options(columns)
                    columns_combo._set_data(columns_combo._get_data())

        # Update column selector widget
        else:
            table = pair_socket.Content.get_data()
            columns_combo = subbox.get_first_child()

            if isdatatable(table):
                columns = table.collect_schema().names()
                self.frame.data[f'{prefix}table'] = table
            else:
                columns = []
                self.frame.data[f'{prefix}table'] = None

            if columns != list(columns_combo.options.keys()):
                columns_combo.set_options(columns)
                columns_combo._set_data(columns_combo._get_data())

        self.frame.is_processing = busy

    def _add_table_combo(self,
                         prefix:    str,
                         tables:    list,
                         content:   NodeContent,
                         container: Gtk.Box,
                         ) ->       NodeComboButton:
        """"""
        column_combo = self._add_column_combo(prefix, [], None)

        prefix = prefix[0]

        def get_data() -> str:
            """"""
            return self.frame.data[f'{prefix}tname']

        def set_data(value: str) -> None:
            """"""
            def callback(value: str) -> None:
                """"""
                busy = self.frame.is_processing
                self.frame.is_processing = True

                sheet = content.get_data()

                if sheet.tables:
                    # Reset selected table if tables changed
                    if value not in sheet.tables:
                        value = next((k for k in sheet.tables.keys()))

                    table = sheet.tables[value][1]
                    columns = table.collect_schema().names()

                    column = self.frame.data[f'{prefix}column']

                    # Reset selected column if columns changed
                    if column not in columns:
                        column = columns[0] if columns else ''

                    self.frame.data[f'{prefix}table']  = table
                    self.frame.data[f'{prefix}tname']  = value
                    self.frame.data[f'{prefix}column'] = column

                    column_combo.set_data(column)
                    column_combo.set_options(columns)
                    column_combo.set_sensitive(len(columns) > 0)

                    column_combo._set_data(column)

                else:
                    column_combo.set_data('')
                    column_combo.set_options([])
                    column_combo.set_sensitive(False)

                    column_combo._set_data('')

                table_combo.set_data(get_data())

                self.frame.is_processing = busy

                self.frame.do_execute(backward = False)

            take_snapshot(self, callback, value)

        table_combo = NodeComboButton(title    = _('Table'),
                                      get_data = get_data,
                                      set_data = set_data,
                                      options  = tables)

        if container:
            container.append(table_combo)
            container.append(column_combo)

        busy = self.frame.is_processing
        self.frame.is_processing = True

        tname = get_data()

        if tables and \
                tname not in tables:
            tname = tables[0]

        set_data(tname)
        column_combo._set_data(column_combo._get_data())

        self.frame.is_processing = busy

        return table_combo

    def _add_column_combo(self,
                          prefix:    str,
                          columns:   list,
                          container: Gtk.Box,
                          ) ->       NodeComboButton:
        """"""
        column_combo = None
        columns_check = None

        prefix = prefix[0]

        def get_data() -> str:
            """"""
            return self.frame.data[f'{prefix}column']

        def set_data(value: str) -> None:
            """"""
            def callback(value: str) -> None:
                """"""
                nonlocal columns_check

                if columns_check:
                    columns_check.unparent()
                    columns_check = None

                all_columns = list(column_combo.options.values())

                if all_columns:
                    # Reset selected column if columns changed
                    if value not in all_columns:
                        value = all_columns[0]

                    # Exclude column from the available columns
                    if value in all_columns:
                        all_columns.remove(value)

                    columns = self.frame.data[f'{prefix}columns']

                    # Reset the available columns if column changed
                    if value != self.frame.data[f'{prefix}column']:
                        columns = all_columns

                    # Filter unvalid columns from selection
                    if columns:
                        new_columns = []
                        for column in all_columns:
                            if column in columns:
                                new_columns.append(column)
                        columns = new_columns

                    # Selection cannot be empty
                    columns = columns or all_columns

                    self.frame.data[f'{prefix}column']  = value
                    self.frame.data[f'{prefix}columns'] = columns

                    if all_columns:
                        columns_check = self._add_columns_check(prefix, all_columns)
                        subbox = column_combo.get_parent()
                        box = subbox.get_parent()
                        box.append(columns_check)

                column_combo.set_data(get_data())

                self.frame.do_execute(backward = False)

            take_snapshot(self, callback, value)

        column_combo = NodeComboButton(title    = _('On Column'),
                                       get_data = get_data,
                                       set_data = set_data,
                                       options  = columns)

        if container:
            container.append(column_combo)

        busy = self.frame.is_processing
        self.frame.is_processing = True

        set_data(get_data())

        self.frame.is_processing = busy

        return column_combo

    def _add_columns_check(self,
                           prefix:  str,
                           columns: list,
                           ) ->     Gtk.Expander:
        """"""
        prefix = prefix[0]

        def get_data() -> list[str]:
            """"""
            return self.frame.data[f'{prefix}columns']

        def set_data(value: list[str]) -> None:
            """"""
            def callback(value: list[str]) -> None:
                """"""
                self.frame.data[f'{prefix}columns'] = value
                self.frame.do_execute(backward = False)

            take_snapshot(self, callback, value)

        group = NodeCheckGroup(get_data = get_data,
                               set_data = set_data,
                               options  = columns)
        expander = Gtk.Expander(label = _('Columns'),
                                child = group)

        def on_expanded(widget:     Gtk.Widget,
                        param_spec: GObject.ParamSpec,
                        ) ->        None:
            """"""
            self.frame.data[f'{prefix}column.exp'] = widget.get_expanded()

        expander.connect('notify::expanded', on_expanded)

        if self.frame.data[f'{prefix}column.exp']:
            expander.set_expanded(True)

        return expander