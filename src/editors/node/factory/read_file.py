# read_file.py
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
from ._utils import iscompatible
from ._utils import take_snapshot

from ..content import NodeContent
from ..frame import NodeFrame
from ..frame import NodeFrameType
from ..socket import NodeSocket
from ..socket import NodeSocketType
from ..widgets import NodeCheckButton
from ..widgets import NodeCheckGroup
from ..widgets import NodeComboButton
from ..widgets import NodeFileReader
from ..widgets import NodeLabel
from ..widgets import NodeSpinButton

logger = logging.getLogger(__name__)

class NodeReadFile(NodeTemplate):

    ndname = _('Read File')

    action = 'read-file'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeReadFile(x, y)

        self.frame.node_type  = NodeFrameType.SOURCE
        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['file-path']        = ''
        self.frame.data['all-columns']      = []
        self.frame.data['kwargs']           = {}
        self.frame.data['refresh-columns']  = False
        self.frame.data['column.exp']       = False
        self.frame.data['limiter.exp']      = False
        self.frame.data['refresh-cache']    = True

        self._add_output()
        self._add_chooser()

        def on_refresh(button: Gtk.Button) -> None:
            """"""
            self.frame.data['refresh-cache'] = True
            self.frame.do_execute(backward = False)
        self.frame.CacheButton.connect('clicked', on_refresh)

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        from polars import DataFrame
#       from ....core.constants import SPREADSHEET_FILES

        file_path   = args[0]
        all_columns = args[1]

        self.frame.data['file-path']   = file_path
        self.frame.data['all-columns'] = all_columns
        self.frame.data['kwargs']      = kwargs

        widget = self.frame.contents[1].Widget
        widget.set_data(file_path)

        while len(self.frame.contents) > 2:
            content = self.frame.contents[-1]
            self.frame.remove_content(content)

        if not file_path:
            self.frame.data['table'] = DataFrame()
            self.frame.do_execute(backward = False)
            return

        from ....core.utils import get_file_format
        file_format = get_file_format(file_path)

        # Generate corresponding contents
        match file_format:
            case 'csv' | 'tsv' | 'txt':
                self._add_rows_selector(with_from_rows  = True,
                                        with_has_header = True)
                self._add_delimiters_group(visible = file_format not in {'tsv'})
                self._add_columns_selector()
                self.frame.data['refresh-columns'] = True

            case 'parquet':
                self._add_rows_selector(with_from_rows  = False,
                                        with_has_header = False)
                self._add_columns_selector()
                self.frame.data['refresh-columns'] = True

#           case _ if file_format in SPREADSHEET_FILES:
#               ...

        self.frame.data['refresh-cache'] = True

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        file_path = self.frame.data.get('file-path')

        if not file_path:
            return

        if not self.frame.data['refresh-cache']:
            return

        kwargs = self.frame.data['kwargs']
        kwargs = deepcopy(kwargs)

        # Do not include the columns when taking a sample
        del kwargs['columns']

        has_error = False
        self.frame.ErrorButton.set_visible(False)

        # Read file at the given path with pre-processed args
        from polars import LazyFrame
        from ....backend.file import File
        try:
            result = File.read(file_path, **kwargs)
            if isinstance(result, LazyFrame):
                result.head(1_000).collect()

        except FileNotFoundError:
            text = f'{_('File not found')}: {file_path}'
            self.frame.ErrorButton.set_tooltip_text(text)
            self.frame.ErrorButton.set_visible(True)
            return
        except:
            has_error = True

        if has_error:
            from ....core.utils import get_file_format
            file_format = get_file_format(file_path)
            file_format = file_format or 'csv'

            # Unless it's a text file, we won't retry
            # to read the file after the last failure
            if file_format not in {'csv', 'tsv', 'txt'}:
                has_error = False

        if has_error:
            # Retry by ignoring any errors
            kwargs['ignore_errors'] = True
            kwargs['infer_schema'] = False

            try:
                result = File.read(file_path, **kwargs)
                if isinstance(result, LazyFrame):
                    result.head(1_000).collect()
                has_error = False

            except Exception as e:
                self.frame.ErrorButton.set_tooltip_text(str(e))
                self.frame.ErrorButton.set_visible(True)

        if has_error:
            # We use non-standard parameters to force loading the entire file
            # contents into one table column without losing any data. This is
            # an opinionated solution indeed. But anyway, let the user decide
            # what to do next.
            kwargs['separator'] = '\x1f'
            kwargs['truncate_ragged_lines'] = True
            kwargs['quote_char'] = None

            try:
                result = File.read(file_path, **kwargs)
                if isinstance(result, LazyFrame):
                    result.head(1_000).collect()
                has_error = False

            except Exception as e:
                self.frame.ErrorButton.set_tooltip_text(str(e))
                self.frame.ErrorButton.set_visible(True)

        if has_error:
            from polars import DataFrame
            result = DataFrame()

#       # Post-process the resulting data
#       from fastexcel import ExcelReader
#       if isinstance(result, ExcelReader):
#           pass

        table_columns = result.collect_schema().names()
        self.frame.data['all-columns'] = table_columns

        cur_columns = self.frame.data['kwargs']['columns']

        if table_columns and cur_columns:
            # Filter unvalid columns from selection
            new_columns = []
            for column in table_columns:
                if column in cur_columns:
                    new_columns.append(column)
            new_columns = new_columns or table_columns
            self.frame.data['kwargs']['columns'] = new_columns

            # Apply the columns filter
            kwargs['columns'] = new_columns
            result = result.select(kwargs['columns'])

        if not cur_columns:
            self.frame.data['kwargs']['columns'] = table_columns

        if self.frame.data['refresh-columns']:
            content = self.frame.contents[-1]
            self.frame.remove_content(content)
            if table_columns:
                self._add_columns_selector()

        if self.frame.data['column.exp']:
            widget = self.frame.contents[-1].Widget
            widget.set_expanded(True)

        self.frame.data['refresh-columns'] = False

        self.frame.data['table'] = result

        self.frame.data['refresh-cache'] = False
        self.frame.CacheButton.set_visible(True)

    def do_save(self) -> dict:
        """"""
        return {
            'file-path':   self.frame.data['file-path'],
            'all-columns': deepcopy(self.frame.data['all-columns']),
            'kwargs':      deepcopy(self.frame.data['kwargs']),
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            file_path   = value['file-path']
            all_columns = value['all-columns']
            kwargs      = value['kwargs']
            self.set_data(file_path, all_columns, **kwargs)

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

    def _add_chooser(self) -> None:
        """"""
        def get_data() -> str:
            """"""
            return self.frame.data['file-path']

        def set_data(*args, **kwargs) -> None:
            """"""
            take_snapshot(self, self.set_data, *args, **kwargs)

        chooser = NodeFileReader(get_data = get_data,
                                 set_data = set_data)
        self.frame.add_content(chooser)

    def _add_delimiters_group(self,
                              visible: bool = True,
                              ) ->     None:
        """"""
        box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL,
                      visible     = visible)
        box.add_css_class('linked')

        box.append(self._add_column_separator())
        box.append(self._add_quote_character())
        box.append(self._add_decimal_separator())

        expander = Gtk.Expander(label = _('Delimiters'),
                                child = box)
        self.frame.add_content(expander)

        if self.frame.data['limiter.exp']:
            expander.set_expanded(True)

    def _add_column_separator(self) -> None:
        """"""
        def get_data() -> str:
            """"""
            return self.frame.data['kwargs']['separator']

        def set_data(value: str) -> None:
            """"""
            def callback(value: str) -> None:
                """"""
                self.frame.data['kwargs']['separator'] = value
                self.frame.data['refresh-columns'] = True
                self.frame.data['refresh-cache'] = True
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        from ....ui.file_import.view_csv import SEPARATOR_OPTS
        combo = NodeComboButton(title    = _('Column Separator'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = SEPARATOR_OPTS)

        return combo

    def _add_quote_character(self) -> None:
        """"""
        def get_data() -> str:
            """"""
            return self.frame.data['kwargs']['quote_char']

        def set_data(value: str) -> None:
            """"""
            def callback(value: str) -> None:
                """"""
                self.frame.data['kwargs']['quote_char'] = value
                self.frame.data['refresh-columns'] = True
                self.frame.data['refresh-cache'] = True
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        from ....ui.file_import.view_csv import QUOTE_CHAR_OPTS
        combo = NodeComboButton(title    = _('Quote Character'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = QUOTE_CHAR_OPTS)

        return combo

    def _add_decimal_separator(self) -> None:
        """"""
        def get_data() -> str:
            """"""
            return self.frame.data['kwargs']['decimal_comma']

        def set_data(value: str) -> None:
            """"""
            def callback(value: str) -> None:
                """"""
                self.frame.data['kwargs']['decimal_comma'] = value
                self.frame.data['refresh-columns'] = True
                self.frame.data['refresh-cache'] = True
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        from ....ui.file_import.view_csv import DECIMAL_COMMA_OPTS
        combo = NodeComboButton(title    = _('Decimal Separator'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = DECIMAL_COMMA_OPTS)

        return combo

    def _add_rows_selector(self,
                           with_from_rows:  bool = True,
                           with_has_header: bool = True,
                           ) ->             None:
        """"""
        self._add_no_rows()

        if with_from_rows:
            self._add_from_row()

        if with_has_header:
            self._add_has_header()

    def _add_no_rows(self) -> None:
        """"""
        def get_data() -> int:
            """"""
            return self.frame.data['kwargs']['n_rows'] or 0

        def set_data(value: int) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                self.frame.data['kwargs']['n_rows'] = value or None
                self.frame.data['refresh-cache'] = True
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        spin = NodeSpinButton(title    = _('No. Rows'),
                              get_data = get_data,
                              set_data = set_data,
                              lower    = 0,
                              digits   = 0)
        socket_type = NodeSocketType.INPUT
        content = self.frame.add_content(widget      = spin,
                                         socket_type = socket_type,
                                         data_type   = int,
                                         get_data    = get_data,
                                         set_data    = set_data)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            content.Widget.set_visible(False)

            label = NodeLabel(_('No. Rows'), can_link = True)
            label.insert_after(content.Container, content.Socket)

            if not iscompatible(pair_socket, self_content):
                return

            self.frame.data['n_rows.bak'] = content.get_data()

            self.frame.data['refresh-cache'] = True

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            if 'n_rows.bak' in self.frame.data:
                content.set_data(self.frame.data['n_rows.bak'])

            self.frame.data['refresh-cache'] = True

            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink

    def _add_from_row(self) -> None:
        """"""
        def get_data() -> int:
            """"""
            return self.frame.data['kwargs']['skip_rows'] + 1

        def set_data(value: int) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                self.frame.data['kwargs']['skip_rows'] = value - 1
                self.frame.data['refresh-cache'] = True
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        spin = NodeSpinButton(title    = _('From Row'),
                              get_data = get_data,
                              set_data = set_data,
                              lower    = 1,
                              digits   = 0)
        socket_type = NodeSocketType.INPUT
        content = self.frame.add_content(widget      = spin,
                                         socket_type = socket_type,
                                         data_type   = int,
                                         get_data    = get_data,
                                         set_data    = set_data)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            content.Widget.set_visible(False)

            label = NodeLabel(_('From Row'), can_link = True)
            label.insert_after(content.Container, content.Socket)

            if not iscompatible(pair_socket, self_content):
                return

            self.frame.data['skip_rows.bak'] = content.get_data()

            self.frame.data['refresh-cache'] = True

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            if 'skip_rows.bak' in self.frame.data:
                content.set_data(self.frame.data['skip_rows.bak'])

            self.frame.data['refresh-cache'] = True

            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink

    def _add_has_header(self) -> None:
        """"""
        def get_data() -> bool:
            """"""
            return self.frame.data['kwargs']['has_header']

        def set_data(value: bool) -> None:
            """"""
            def callback(value: bool) -> None:
                """"""
                if self.frame.data['kwargs']['has_header'] != value:
                    self.frame.data['kwargs']['has_header'] = value
                    self.frame.data['refresh-columns'] = True
                    self.frame.data['refresh-cache'] = True
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        check = NodeCheckButton(title    = _('First Row as Header'),
                                get_data = get_data,
                                set_data = set_data)
        socket_type = NodeSocketType.INPUT
        content = self.frame.add_content(widget      = check,
                                         socket_type = socket_type,
                                         data_type   = bool,
                                         get_data    = get_data,
                                         set_data    = set_data)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            content.Widget.set_visible(False)

            label = NodeLabel(_('First Row as Header'), can_link = True)
            label.insert_after(content.Container, content.Socket)

            if not iscompatible(pair_socket, self_content):
                return

            self.frame.data['has_header.bak'] = content.get_data()

            self.frame.data['refresh-cache'] = True

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            if 'has_header.bak' in self.frame.data:
                content.set_data(self.frame.data['has_header.bak'])

            self.frame.data['kwargs']['columns'] = []
            self.frame.data['refresh-cache'] = True

            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink

    def _add_columns_selector(self) -> None:
        """"""
        def get_data() -> list[str]:
            """"""
            return self.frame.data['kwargs']['columns']

        def set_data(value: list[str]) -> None:
            """"""
            def callback(value: list[str]) -> None:
                """"""
                self.frame.data['kwargs']['columns'] = value
                self.frame.data['refresh-cache'] = True
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

        if self.frame.data['column.exp']:
            expander.set_expanded(True)