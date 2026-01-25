# repository.py
#
# Copyright 2025 Naufan Rusyda Faikar
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
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Pango
from polars import DataFrame
from polars import LazyFrame
from typing import Any
import gc

from ..core.utils import generate_uuid
from ..core.utils import unique_name

from .action import ActionEditNode
from .data_type import Sheet
from .frame import NodeFrame
from .content import NodeContent
from .socket import NodeSocket
from .socket import NodeSocketType
from .widget import NodeCheckButton
from .widget import NodeCheckGroup
from .widget import NodeComboButton
from .widget import NodeEntry
from .widget import NodeFileChooser
from .widget import NodeLabel
from .widget import NodeSpinButton

def _iscompatible(pair_socket:  NodeSocket,
                  self_content: NodeContent,
                  ) ->          bool:
    """"""
    self_socket = self_content.Socket

    if not (pair_socket.data_type or self_socket.data_type):
        compatible = True
    else:
        compatible = pair_socket.data_type == self_socket.data_type

    link = self_socket.links[0]
    link.compatible = compatible

    return compatible


def _isreconnected(pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          bool:
    """"""
    incoming_node_uid = id(pair_socket.Frame)

    if self_content.node_uid == incoming_node_uid:
        return True

    self_content.node_uid = incoming_node_uid

    return False


def _take_snapshot(node:     'NodeTemplate',
                   callback: 'callable',
                   *args:    'list',
                   **kwargs: 'dict',
                   ) ->      'None':
    """"""

    old_data = node.do_save()
    callback(*args, **kwargs)
    new_data = node.do_save()

    editor = node.frame.get_editor()
    values = (old_data, new_data)
    action = ActionEditNode(editor, node.frame, values)
    editor.do(action, add_only = True)



class NodeTemplate():

    ndname = _('Template')

    action = ''

    def __init__(self,
                 x:    int = 0,
                 y:    int = 0,
                 name: str = None,
                 ) ->  None:
        """"""
        if name:
            self.ndname = name

        self.frame = NodeFrame(title  = self.ndname,
                               x      = x,
                               y      = y,
                               parent = self)

        self.frame.data = {} # internal use only

    @staticmethod
    def new(cls: object,
            x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        return NodeFrame(cls.ndname, x, y)

    def clone(self) -> NodeFrame:
        """"""
        value = self.frame.do_save()
        frame = self.__class__.new(self.frame.x + 30,
                                   self.frame.y + 30)
        frame.do_restore(value)
        return frame

    def add_data(self,
                 value: Any,
                 ) ->   str:
        """"""
        uuid = generate_uuid()
        self.frame.data[uuid] = value
        return uuid



class NodeBoolean(NodeTemplate):

    ndname = _('Boolean')

    action = 'new-boolean'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeBoolean(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['value'] = False

        self._add_output()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['value'] = args[0]

        widget = self.frame.contents[0].Widget
        widget.set_data(args[0])

        self.frame.do_execute(backward = False)

    def do_save(self) -> bool:
        """"""
        return self.frame.data['value']

    def do_restore(self,
                   value: bool,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except:
            pass # TODO: show errors to user

    def _add_output(self) -> None:
        """"""
        def get_data() -> bool:
            """"""
            return self.frame.data['value']

        def set_data(value: bool) -> None:
            """"""
            _take_snapshot(self, self.set_data, value)

        check = NodeCheckButton(title    = _('Value'),
                                get_data = get_data,
                                set_data = set_data)
        socket_type = NodeSocketType.OUTPUT
        self.frame.add_content(widget      = check,
                               socket_type = socket_type,
                               data_type   = bool,
                               get_data    = get_data,
                               set_data    = set_data)



class NodeDecimal(NodeTemplate):

    ndname = _('Decimal')

    action = 'new-decimal'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeDecimal(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['value'] = 0.0

        self._add_output()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['value'] = args[0]

        widget = self.frame.contents[0].Widget
        widget.set_data(args[0])

        self.frame.do_execute(backward = False)

    def do_save(self) -> float:
        """"""
        return self.frame.data['value']

    def do_restore(self,
                   value: float,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except:
            pass # TODO: show errors to user

    def _add_output(self) -> None:
        """"""
        def get_data() -> float:
            """"""
            return self.frame.data['value']

        def set_data(value: float) -> None:
            """"""
            _take_snapshot(self, self.set_data, value)

        spin = NodeSpinButton(title    = _('Value'),
                              get_data = get_data,
                              set_data = set_data,
                              lower    = 0)
        socket_type = NodeSocketType.OUTPUT
        self.frame.add_content(widget      = spin,
                               socket_type = socket_type,
                               data_type   = float,
                               get_data    = get_data,
                               set_data    = set_data)



class NodeInteger(NodeTemplate):

    ndname = _('Integer')

    action = 'new-integer'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeInteger(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['value'] = 0

        self._add_output()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['value'] = args[0]

        widget = self.frame.contents[0].Widget
        widget.set_data(args[0])

        self.frame.do_execute(backward = False)

    def do_save(self) -> int:
        """"""
        return self.frame.data['value']

    def do_restore(self,
                   value: int,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except:
            pass # TODO: show errors to user

    def _add_output(self) -> None:
        """"""
        def get_data() -> int:
            """"""
            return self.frame.data['value']

        def set_data(value: int) -> None:
            """"""
            _take_snapshot(self, self.set_data, value)

        spin = NodeSpinButton(title    = _('Value'),
                              get_data = get_data,
                              set_data = set_data,
                              lower    = 0,
                              digits   = 0)
        socket_type = NodeSocketType.OUTPUT
        self.frame.add_content(widget      = spin,
                               socket_type = socket_type,
                               data_type   = int,
                               get_data    = get_data,
                               set_data    = set_data)



class NodeString(NodeTemplate):

    ndname = _('String')

    action = 'new-string'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeString(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['value'] = ''

        self._add_output()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['value'] = args[0]

        widget = self.frame.contents[0].Widget
        widget.set_data(args[0])

        self.frame.do_execute(backward = False)

    def do_save(self) -> str:
        """"""
        return self.frame.data['value']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except:
            pass # TODO: show errors to user

    def _add_output(self) -> None:
        """"""
        def get_data() -> str:
            """"""
            return self.frame.data['value']

        def set_data(value: str) -> None:
            """"""
            _take_snapshot(self, self.set_data, value)

        entry = NodeEntry(get_data, set_data)
        socket_type = NodeSocketType.OUTPUT
        self.frame.add_content(widget      = entry,
                               socket_type = socket_type,
                               data_type   = str,
                               get_data    = get_data,
                               set_data    = set_data)



class NodeReadFile(NodeTemplate):

    ndname = _('Read File')

    action = 'read-file'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeReadFile(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['file-path']       = ''
        self.frame.data['all-columns']     = []
        self.frame.data['kwargs']          = {}
        self.frame.data['refresh-columns'] = False
        self.frame.data['column-expanded'] = False

        self._add_output_table()
        self._add_file_chooser()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
#       from ..file_import_window import SPREADSHEET_FILES

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

        # TODO: re-link all previous sockets

        if not file_path:
            self.frame.data['table'] = DataFrame()
            self.frame.do_execute(backward = False)
            return

        from ..core.utils import get_file_format
        file_format = get_file_format(file_path)

        # Generate corresponding contents
        match file_format:
            case 'csv' | 'tsv' | 'txt':
                self._add_file_delimiter()
                self._add_rows_selector(with_from_rows  = True,
                                        with_has_header = True)
                self._add_columns_selector()

            case 'parquet':
                self._add_rows_selector(with_from_rows  = False,
                                        with_has_header = False)
                self._add_columns_selector()

#           case _ if file_format in SPREADSHEET_FILES:
#               ...

        if file_format in {'csv', 'tsv', 'txt', 'parquet'}:
            if self.frame.data['column-expanded']:
                widget = self.frame.contents[-1].Widget
                widget.set_expanded(True)

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        file_path = self.frame.data.get('file-path')

        if not file_path:
            return

        self.frame.is_processing = True
        # Prevents recursive processing
        # when setting node socket data

        # Resetting data by incoming input nodes
        for self_content in self.frame.contents:
            if not (self_socket := self_content.Socket):
                continue
            if not self_socket.is_input():
                continue
            if not (links := self_socket.links):
                continue
            if not links[0].compatible:
                continue
            pair_socket = links[0].in_socket
            pair_content = pair_socket.Content
            value = pair_content.get_data()
            self_content.set_data(value)

        if self.frame.data['refresh-columns']:
            self.frame.data['kwargs']['columns'] = []

        kwargs = self.frame.data['kwargs']
        kwargs = deepcopy(kwargs)

        # Remove the `columns` argument when it's an empty list
        # to prevent loading an empty dataframe from the source
        if 'columns' in kwargs and not kwargs['columns']:
            del kwargs['columns']

        has_error = False

        # Read file at the given path with pre-processed args
        from polars import LazyFrame
        from ..core.file_manager import FileManager
        try:
            result = FileManager.read_file(file_path, **kwargs)
            if isinstance(result, LazyFrame):
                result.head(1_000).collect()
        except:
            has_error = True

        if has_error:
            from ..core.utils import get_file_format
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
                result = FileManager.read_file(file_path, **kwargs)
                if isinstance(result, LazyFrame):
                    result.head(1_000).collect()
                has_error = False
            except:
                pass # TODO: show errors to user

        if has_error:
            # We use non-standard parameters to force loading the entire file contents
            # into one column without losing any data. This is an opinionated solution
            # indeed. But anyway, let's the user decide what to do next.
            kwargs['separator'] = '\x1f'
            kwargs['truncate_ragged_lines'] = True
            kwargs['quote_char'] = None

            try:
                result = FileManager.read_file(file_path, **kwargs)
                if isinstance(result, LazyFrame):
                    result.head(1_000).collect()
            except:
                pass # TODO: show errors to user

        if result is None:
            result = DataFrame()

#       # Post-process the resulting data
#       from fastexcel import ExcelReader
#       if isinstance(result, ExcelReader):
#           pass
#       else:
        content = self.frame.contents[0]
        content.set_data(result)

        if isinstance(result, LazyFrame):
            table_columns = result.collect_schema().names()
        else:
            table_columns = result.columns

        # Repopulate the column list if necessary only
        # to prevent any unwanted glitches for example
        # content is being collapsed on toggling items
        if 'columns' not in kwargs:
#           from ..core.utils import get_file_format
#           from ..file_import_window import SPREADSHEET_FILES
#           file_format = get_file_format(self.file_path)
#           if file_format not in SPREADSHEET_FILES:
            self.frame.data['all-columns'] = table_columns
            self.frame.data['kwargs']['columns'] = table_columns

        if self.frame.data['refresh-columns']:
            content = self.frame.contents[-1]
            self.frame.remove_content(content)
            self._add_columns_selector()

            if self.frame.data['column-expanded']:
                widget = self.frame.contents[-1].Widget
                widget.set_expanded(True)

        self.frame.data['refresh-columns'] = False

        self.frame.is_processing = False

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
        except:
            pass # TODO: show errors to user

    def _add_output_table(self) -> None:
        """"""
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

    def _add_file_chooser(self) -> None:
        """"""
        def get_data() -> str:
            """"""
            return self.frame.data['file-path']

        def on_clicked(button: Gtk.Button) -> None:
            """"""
            def callback(*args, **kwargs) -> None:
                """"""
                _take_snapshot(self, self.set_data, *args, **kwargs)
            from ..file_manager import FileManager
            window = self.frame.get_root()
            FileManager.open_file(window, callback)

        chooser = NodeFileChooser(get_data   = get_data,
                                  on_clicked = on_clicked)
        self.frame.add_content(chooser)

    def _add_file_delimiter(self) -> None:
        """"""
        box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        box.add_css_class('linked')
        self.frame.add_content(box)

        # TODO: hide column-separator widget for TSV file

        self._add_column_separator(box)
        self._add_quote_character(box)
        self._add_decimal_separator(box)

    def _add_column_separator(self,
                              container: Gtk.Widget,
                              ) ->       None:
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
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        from ..file_import_csv_view import SEPARATOR_OPTS
        combo = NodeComboButton(title    = _('Column Separator'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = SEPARATOR_OPTS)
        container.append(combo)

    def _add_quote_character(self,
                             container: Gtk.Widget,
                             ) ->       None:
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
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        from ..file_import_csv_view import QUOTE_CHAR_OPTS
        combo = NodeComboButton(title    = _('Quote Character'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = QUOTE_CHAR_OPTS)
        container.append(combo)

    def _add_decimal_separator(self,
                               container: Gtk.Widget,
                               ) ->       None:
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
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        from ..file_import_csv_view import DECIMAL_COMMA_OPTS
        combo = NodeComboButton(title    = _('Decimal Separator'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = DECIMAL_COMMA_OPTS)
        container.append(combo)

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
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

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

            label = NodeLabel(_('No. Rows'), linked = True)
            label.insert_after(content.Container, content.Socket)

            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

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
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

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

            label = NodeLabel(_('From Row'), linked = True)
            label.insert_after(content.Container, content.Socket)

            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

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
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

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

            label = NodeLabel(_('First Row as Header'), linked = True)
            label.insert_after(content.Container, content.Socket)

            if not _iscompatible(pair_socket, self_content):
                return

            # Save the socket value
            kwargs = self.frame.data['kwargs']
            self.frame.data['has-header'] = kwargs['has_header']

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            # Restore the socket value
            kwargs = self.frame.data['kwargs']
            kwargs['has_header'] = self.frame.data['has-header']
            kwargs['columns'] = [] # reset the specified column names

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
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        group = NodeCheckGroup(get_data = get_data,
                               set_data = set_data,
                               options  = self.frame.data['all-columns'])
        expander = Gtk.Expander(label = _('Columns'),
                                child = group)
        self.frame.add_content(expander, None)

        def on_expanded(widget:     Gtk.Widget,
                        param_spec: GObject.ParamSpec,
                        ) ->        None:
            """"""
            self.frame.data['column-expanded'] = expander.get_expanded()

        expander.connect('notify::expanded', on_expanded)



class NodeSheet(NodeTemplate):

    ndname = _('Sheet')

    action = 'new-sheet'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeSheet(x, y)

        self.frame.has_data   = self.has_data
        self.frame.has_view   = self.has_view
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['replace-tables'] = {}

        self._add_output()
        self._add_input()

        return self.frame

    def has_data(self) -> bool:
        """"""
        contents = self.frame.contents[:-1]
        for content in contents:
            if not content.Socket:
                continue
            if content.Socket.is_input():
                return True
        return False

    def has_view(self) -> bool:
        """"""
        content = self.frame.contents[0]
        for link in content.Socket.links:
            if not link.compatible:
                continue
            frame = link.out_socket.Frame
            if isinstance(frame.parent, NodeViewer):
                return True
        return False

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        value = self.frame.data['value']
        value.tables = []

        for self_content in self.frame.contents[1:-1]:
            box = self_content.Widget
            label = box.get_first_child()
            title = label.get_label()
            if title not in self.frame.data:
                continue

            self_socket = self_content.Socket
            if links := self_socket.links:
                pair_socket = links[0].in_socket
                pair_content = pair_socket.Content
                table = pair_content.get_data()
                coordinate = self.frame.data[title]
                value.tables.append((coordinate, table))

    def do_save(self) -> list:
        """"""
        values = []
        for content in self.frame.contents[1:-1]:
            box = content.Widget
            label = box.get_first_child()
            title = label.get_label()
            position = self.frame.data[title]
            value = {
                'title':    title,
                'position': position,
            }
            values.append(value)
        return values

    def do_restore(self,
                   values: list,
                   ) ->    None:
        """"""
        try:
            for index, value in enumerate(values):
                index += 1 # input socket starts from index 1
                n_ready_inputs = len(self.frame.contents) - 2
                if index <= n_ready_inputs:
                    widget = self.frame.contents[index].Widget
                    widget.set_data(value['position'])
                else:
                    tables = self.frame.data['replace-tables']
                    tables[index] = value
        except:
            pass # TODO: show errors to user

        self.frame.do_execute(backward = False)

    def _add_output(self) -> None:
        """"""
        self.frame.data['value'] = Sheet()

        def get_data() -> Sheet:
            """"""
            return self.frame.data['value']

        def set_data(value: Sheet) -> None:
            """"""
            self.frame.data['value'] = value
            self.frame.do_execute(backward = False)

        widget = NodeLabel(_('Value'))
        socket_type = NodeSocketType.OUTPUT
        self.frame.add_content(widget      = widget,
                               socket_type = socket_type,
                               data_type   = Sheet,
                               get_data    = get_data,
                               set_data    = set_data)

    def _add_input(self) -> None:
        """"""
        widget = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        widget.set_data = lambda *args: None

        label = NodeLabel(_('Table'))
        label.set_xalign(0.0)
        label.set_opacity(0.0)
        widget.append(label)

        socket_type = NodeSocketType.INPUT
        content = self.frame.add_content(widget      = widget,
                                         socket_type = socket_type,
                                         data_type   = DataFrame,
                                         placeholder = True,
                                         auto_remove = True)

        def restore_data(title:   str,
                         content: NodeContent) -> str:
            """"""
            cindex = self.frame.contents.index(content)
            tables = self.frame.data['replace-tables']
            if cindex in tables:
                title = tables[cindex]['title']
                position = tables[cindex]['position']
                label.set_label(title)
                self.frame.data[title] = tuple(position)
                del tables[cindex]
            return title

        def replace_widget(title: str) -> None:
            """"""
            container = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
            container.add_css_class('linked')

            if title not in self.frame.data:
                self.frame.data[title] = (1, 1) # column, row

            spin_col = self._add_col_spin(title)
            spin_row = self._add_row_spin(title)

            container.append(spin_col)
            container.append(spin_row)

            expander = Gtk.Expander(label = label.get_label(),
                                    child = container)
            widget.append(expander)

            def set_data(value: tuple) -> None:
                """"""
                col, row = value
                spin_col.set_data(col)
                spin_row.set_data(row)
                self.frame.data[title] = value

            widget.set_data = set_data

            label.set_visible(False)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            old_title = label.get_label()

            # Generate the socket label based on the connected node
            titles = [content.Widget.get_first_child().get_label()
                      for content in self.frame.contents[1:-1]
                      if content != self_content]
            new_title = unique_name(_('Table'), titles)
            label.set_label(new_title)
            label.set_opacity(1.0)

            if not _iscompatible(pair_socket, self_content):
                if self_content.placeholder:
                    self_content.placeholder = False
                    self._add_input()
                return

            if _isreconnected(pair_socket, self_content):
                label.set_label(old_title)
                return # skip if the pending socket to be removed
                       # get connected again to the previous node

            new_title = restore_data(new_title, self_content)

            if self_content.placeholder:
                self_content.placeholder = False
                replace_widget(new_title)
                self._add_input()

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink

        def do_remove(content: NodeContent) -> None:
            """"""
            title = label.get_label()
            if title in self.frame.data:
                del self.frame.data[title]

            content.node_uid = None
            self.frame.remove_content(content)

            del content
            gc.collect()

        content.do_remove = do_remove

    def _add_col_spin(self,
                      title: str,
                      ) ->   NodeSpinButton:
        """"""
        def get_data() -> int:
            """"""
            return self.frame.data[title][0]

        def set_data(value: int) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                _, row = self.frame.data[title]
                self.frame.data[title] = (value, row)
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        spin = NodeSpinButton(title    = _('Column'),
                              get_data = get_data,
                              set_data = set_data,
                              lower    = 1,
                              digits   = 0)

        return spin

    def _add_row_spin(self,
                      title: str,
                      ) ->   NodeSpinButton:
        """"""
        def get_data() -> int:
            """"""
            return self.frame.data[title][1]

        def set_data(value: int) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                col, _ = self.frame.data[title]
                self.frame.data[title] = (col, value)
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        spin = NodeSpinButton(title    = _('Row'),
                              get_data = get_data,
                              set_data = set_data,
                              lower    = 1,
                              digits   = 0)

        return spin



class NodeViewer(NodeTemplate):

    ndname = _('Viewer')

    action = 'new-viewer'

    SUPPORTED_VIEWS = {Sheet}

    PRIMITIVE_TYPES = {bool, float, int, str}

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeViewer(x, y)

        self.frame.is_active  = self.is_active
        self.frame.set_active = self.set_active
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['is-active']      = False
        self.frame.data['replace-titles'] = {}

        self._add_input()

        return self.frame

    def is_active(self) -> bool:
        """"""
        return self.frame.data['is-active']

    def set_active(self,
                   active: bool,
                   ) ->    None:
        """"""
        self.frame.data['is-active'] = active

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        if not pair_socket:
            return

        pair_content = pair_socket.Content
        value = pair_content.get_data()

        for link in pair_socket.links:
            if link.out_socket.Frame != self.frame:
                continue
            self_content = link.out_socket.Content

            label = self_content.Widget

            if pair_socket.data_type == Sheet:
                if not self_content.Page:
                    continue
                editor = self_content.Page.get_child()
                editor.set_data(value.tables, value.sparse)

            elif pair_socket.data_type in self.PRIMITIVE_TYPES:
                label.set_label(str(value) or f'[{_('Empty')}]')

            elif pair_socket.data_type in {DataFrame}:
                if isinstance(value, LazyFrame):
                    value = value.collect()
                label.set_label(str(value))

            else:
                label.set_label(f'[{_('Object')}]')

    def do_save(self) -> list:
        """"""
        values = []
        for content in self.frame.contents[:-1]:
            label = content.Widget
            value = label.get_label()
            values.append(value)
        return values

    def do_restore(self,
                   values: list,
                   ) ->    None:
        """"""
        try:
            for index, value in enumerate(values):
                titles = self.frame.data['replace-titles']
                titles[index] = value
        except:
            pass # TODO: show errors to user

    def _add_input(self) -> None:
        """"""
        label = Gtk.Label(label     = _('Any'),
                          xalign    = 0.0,
                          opacity   = 0.0,
                          ellipsize = Pango.EllipsizeMode.END)
        label.add_css_class('node-label')
        socket_type = NodeSocketType.INPUT
        content = self.frame.add_content(label,
                                         socket_type,
                                         placeholder = True,
                                         auto_remove = True)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            if _isreconnected(pair_socket, self_content):
                if pair_socket.data_type in self.SUPPORTED_VIEWS:
                    return # skip if the pending socket to be removed
                           # get connected again to the previous node

            if pair_socket.data_type in self.SUPPORTED_VIEWS:
                # Automatically generate the socket label
                titles = [content.Widget.get_label()
                          for content in self.frame.contents[:-1]
                          if content != self_content]
                title = pair_socket.data_type.__name__
                title = unique_name(title, titles)
                label.set_label(title)

            elif pair_socket.data_type in self.PRIMITIVE_TYPES:
                label.set_ellipsize(Pango.EllipsizeMode.NONE)

                if pair_socket.data_type == str:
                    label.set_wrap(True)
                    label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)

            elif pair_socket.data_type in {DataFrame}:
                label.add_css_class('monospace')
                label.set_ellipsize(Pango.EllipsizeMode.NONE)

            else:
                pass

            # Restore content data
            cindex = self.frame.contents.index(self_content)
            titles = self.frame.data['replace-titles']
            if cindex in titles:
                title = titles[cindex]
                label.set_label(title)
                del titles[cindex]

            label.set_opacity(1.0)

            if self_content.Page:
                window = self.frame.get_root()
                window.TabView.close_page(self_content.Page)
                self_content.Page = None

            def add_sheet_editor() -> bool:
                """"""
                from ..sheet.editor import SheetEditor

                if window := self.frame.get_root():
                    frame = pair_socket.Frame
                    sheet = pair_socket.Content.get_data()
                    editor = SheetEditor(title,
                                         sheet.tables,
                                         sheet.sparse,
                                         frame = frame)
                    self_content.Page = window.add_new_editor(editor)
                    return Gdk.EVENT_PROPAGATE

                return Gdk.EVENT_STOP

            if pair_socket.data_type == Sheet:
                GLib.idle_add(add_sheet_editor)

            if self_content.placeholder:
                self_content.placeholder = False
                self._add_input()

            self.frame.do_execute(pair_socket,
                                  self_content,
                                  specified = True)

        content.do_link = do_link

        def do_remove(content: NodeContent) -> None:
            """"""
            content.node_uid = None

            self.frame.remove_content(content)

            if content.Page:
                window = self.frame.get_root()
                window.TabView.close_page(content.Page)
                content.Page = None

            del content
            gc.collect()

        content.do_remove = do_remove



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
        self.frame.data['column-expanded'] = False

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
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_selector()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_selector()

        if isinstance(table, LazyFrame):
            table_columns = table.collect_schema().names()
        else:
            table_columns = table.columns

        if table_columns:
            if columns := self.frame.data['columns']:
                sorted = []
                for column in table_columns:
                    if column in columns:
                        sorted.append(column)
                if sorted:
                    table = table.select(sorted)

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
        except:
            pass # TODO: show errors to user

    def _add_output(self) -> None:
        """"""
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
        label = NodeLabel(_('Table'))
        label.set_xalign(0.0)
        socket_type = NodeSocketType.INPUT
        content = self.frame.add_content(widget      = label,
                                         socket_type = socket_type,
                                         data_type   = DataFrame)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink

    def _refresh_selector(self) -> None:
        """"""
        table = self.frame.data['table']

        # Filter unvalid columns from selection
        if isinstance(table, LazyFrame):
            table_columns = table.collect_schema().names()
        else:
            table_columns = table.columns

        if table_columns:
            if self.frame.data['columns']:
                columns = []
                for column in self.frame.data['columns']:
                    if column in table_columns:
                        columns.append(column)
                columns = columns or table_columns
                self.frame.data['columns'] = columns
            else:
                self.frame.data['columns'] = table_columns

        if self.frame.data['all-columns'] != table_columns:
            self.frame.data['refresh-columns'] = True

        self.frame.data['all-columns'] = table_columns

        if self.frame.data['refresh-columns']:
            if len(self.frame.contents) == 3:
                content = self.frame.contents[-1]
                self.frame.remove_content(content)
            if table_columns:
                self._add_selector()

        if self.frame.data['column-expanded']:
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
            _take_snapshot(self, callback, value)

        group = NodeCheckGroup(get_data = get_data,
                               set_data = set_data,
                               options  = self.frame.data['all-columns'])
        expander = Gtk.Expander(label = _('Columns'),
                                child = group)
        self.frame.add_content(expander, None)

        def on_expanded(widget:     Gtk.Widget,
                        param_spec: GObject.ParamSpec,
                        ) ->        None:
            """"""
            self.frame.data['column-expanded'] = expander.get_expanded()

        expander.connect('notify::expanded', on_expanded)



class NodeRemoveColumns(NodeTemplate):

    ndname = _('Remove Columns')

    action = 'remove-columns'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeRemoveColumns(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['all-columns']     = []
        self.frame.data['columns']         = []
        self.frame.data['refresh-columns'] = False
        self.frame.data['column-expanded'] = False

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
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_selector()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_selector()

        if isinstance(table, LazyFrame):
            table_columns = table.collect_schema().names()
        else:
            table_columns = table.columns

        if table_columns:
            if columns := self.frame.data['columns']:
                sorted = []
                for column in table_columns:
                    if column not in columns:
                        sorted.append(column)
                table = table.select(sorted)

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
        except:
            pass # TODO: show errors to user

    def _add_output(self) -> None:
        """"""
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
        label = NodeLabel(_('Table'))
        label.set_xalign(0.0)
        socket_type = NodeSocketType.INPUT
        content = self.frame.add_content(widget      = label,
                                         socket_type = socket_type,
                                         data_type   = DataFrame)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink

    def _refresh_selector(self) -> None:
        """"""
        table = self.frame.data['table']

        # Filter unvalid columns from selection
        if isinstance(table, LazyFrame):
            table_columns = table.collect_schema().names()
        else:
            table_columns = table.columns

        if table_columns:
            if self.frame.data['columns']:
                columns = []
                for column in self.frame.data['columns']:
                    if column in table_columns:
                        columns.append(column)
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

        if self.frame.data['column-expanded']:
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
            _take_snapshot(self, callback, value)

        group = NodeCheckGroup(get_data = get_data,
                               set_data = set_data,
                               options  = self.frame.data['all-columns'])
        expander = Gtk.Expander(label = _('Columns'),
                                child = group)
        self.frame.add_content(expander, None)

        def on_expanded(widget:     Gtk.Widget,
                        param_spec: GObject.ParamSpec,
                        ) ->        None:
            """"""
            self.frame.data['column-expanded'] = expander.get_expanded()

        expander.connect('notify::expanded', on_expanded)



class NodeKeepTopKRows(NodeTemplate):

    ndname = _('Keep Top K Rows')

    action = 'keep-top-k-rows'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeKeepTopKRows(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['n-rows']          = 0
        self.frame.data['all-columns']     = []
        self.frame.data['columns']         = []
        self.frame.data['refresh-columns'] = False
        self.frame.data['column-expanded'] = False

        self._add_output()
        self._add_input()
        self._add_n_rows()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['n-rows']  = args[0]
        self.frame.data['columns'] = args[1]

        widget = self.frame.contents[2].Widget
        widget.set_data(args[0])

        self.frame.data['refresh-columns'] = True

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_columns()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_columns()

        if table.collect_schema().names():
            if columns := self.frame.data['columns']:
                n_rows = self.frame.data['n-rows']
                table = table.top_k(n_rows, by = columns)

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'n-rows':  self.frame.data['n-rows'],
            'columns': deepcopy(self.frame.data['columns']),
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['n-rows'],
                          value['columns'])
        except:
            pass # TODO: show errors to user

    def _add_output(self) -> None:
        """"""
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
        label = NodeLabel(_('Table'))
        label.set_xalign(0.0)
        socket_type = NodeSocketType.INPUT
        content = self.frame.add_content(widget      = label,
                                         socket_type = socket_type,
                                         data_type   = DataFrame)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink

    def _add_n_rows(self) -> None:
        """"""
        def get_data() -> int:
            """"""
            return self.frame.data['n-rows']

        def set_data(value: int) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                self.frame.data['n-rows'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        spin = NodeSpinButton(title    = _('No. Rows'),
                              get_data = get_data,
                              set_data = set_data,
                              lower    = 0,
                              digits   = 0)
        socket_type = NodeSocketType.INPUT
        self.frame.add_content(widget      = spin,
                               socket_type = socket_type,
                               data_type   = int,
                               get_data    = get_data,
                               set_data    = set_data)

    def _refresh_columns(self) -> None:
        """"""
        table = self.frame.data['table']

        # Filter unvalid columns from selection
        if isinstance(table, LazyFrame):
            table_columns = table.collect_schema().names()
        else:
            table_columns = table.columns

        if table_columns:
            if self.frame.data['columns']:
                columns = []
                for column in self.frame.data['columns']:
                    if column in table_columns:
                        columns.append(column)
                self.frame.data['columns'] = columns

        if self.frame.data['all-columns'] != table_columns:
            self.frame.data['refresh-columns'] = True

        self.frame.data['all-columns'] = table_columns

        if self.frame.data['refresh-columns']:
            if len(self.frame.contents) == 4:
                content = self.frame.contents[-1]
                self.frame.remove_content(content)
            if table_columns:
                self._add_columns()

        if self.frame.data['column-expanded']:
            if len(self.frame.contents) == 4:
                widget = self.frame.contents[-1].Widget
                widget.set_expanded(True)

        self.frame.data['refresh-columns'] = False

    def _add_columns(self) -> None:
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
            _take_snapshot(self, callback, value)

        group = NodeCheckGroup(get_data = get_data,
                               set_data = set_data,
                               options  = self.frame.data['all-columns'])
        expander = Gtk.Expander(label = _('Based On'),
                                child = group)
        self.frame.add_content(expander, None)

        def on_expanded(widget:     Gtk.Widget,
                        param_spec: GObject.ParamSpec,
                        ) ->        None:
            """"""
            self.frame.data['column-expanded'] = expander.get_expanded()

        expander.connect('notify::expanded', on_expanded)



class NodeKeepBottomKRows(NodeTemplate):

    ndname = _('Keep Bottom K Rows')

    action = 'keep-bottom-k-rows'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeKeepBottomKRows(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['n-rows']          = 0
        self.frame.data['all-columns']     = []
        self.frame.data['columns']         = []
        self.frame.data['refresh-columns'] = False
        self.frame.data['column-expanded'] = False

        self._add_output()
        self._add_input()
        self._add_n_rows()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['n-rows']  = args[0]
        self.frame.data['columns'] = args[1]

        widget = self.frame.contents[2].Widget
        widget.set_data(args[0])

        self.frame.data['refresh-columns'] = True

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_columns()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_columns()

        if table.collect_schema().names():
            if columns := self.frame.data['columns']:
                n_rows = self.frame.data['n-rows']
                table = table.bottom_k(n_rows, by = columns)

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'n-rows':  self.frame.data['n-rows'],
            'columns': deepcopy(self.frame.data['columns']),
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['n-rows'],
                          value['columns'])
        except:
            pass # TODO: show errors to user

    def _add_output(self) -> None:
        """"""
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
        label = NodeLabel(_('Table'))
        label.set_xalign(0.0)
        socket_type = NodeSocketType.INPUT
        content = self.frame.add_content(widget      = label,
                                         socket_type = socket_type,
                                         data_type   = DataFrame)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink

    def _add_n_rows(self) -> None:
        """"""
        def get_data() -> int:
            """"""
            return self.frame.data['n-rows']

        def set_data(value: int) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                self.frame.data['n-rows'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        spin = NodeSpinButton(title    = _('No. Rows'),
                              get_data = get_data,
                              set_data = set_data,
                              lower    = 0,
                              digits   = 0)
        socket_type = NodeSocketType.INPUT
        self.frame.add_content(widget      = spin,
                               socket_type = socket_type,
                               data_type   = int,
                               get_data    = get_data,
                               set_data    = set_data)

    def _refresh_columns(self) -> None:
        """"""
        table = self.frame.data['table']

        # Filter unvalid columns from selection
        if isinstance(table, LazyFrame):
            table_columns = table.collect_schema().names()
        else:
            table_columns = table.columns

        if table_columns:
            if self.frame.data['columns']:
                columns = []
                for column in self.frame.data['columns']:
                    if column in table_columns:
                        columns.append(column)
                self.frame.data['columns'] = columns

        if self.frame.data['all-columns'] != table_columns:
            self.frame.data['refresh-columns'] = True

        self.frame.data['all-columns'] = table_columns

        if self.frame.data['refresh-columns']:
            if len(self.frame.contents) == 4:
                content = self.frame.contents[-1]
                self.frame.remove_content(content)
            if table_columns:
                self._add_columns()

        if self.frame.data['column-expanded']:
            if len(self.frame.contents) == 4:
                widget = self.frame.contents[-1].Widget
                widget.set_expanded(True)

        self.frame.data['refresh-columns'] = False

    def _add_columns(self) -> None:
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
            _take_snapshot(self, callback, value)

        group = NodeCheckGroup(get_data = get_data,
                               set_data = set_data,
                               options  = self.frame.data['all-columns'])
        expander = Gtk.Expander(label = _('Based On'),
                                child = group)
        self.frame.add_content(expander, None)

        def on_expanded(widget:     Gtk.Widget,
                        param_spec: GObject.ParamSpec,
                        ) ->        None:
            """"""
            self.frame.data['column-expanded'] = expander.get_expanded()

        expander.connect('notify::expanded', on_expanded)



class NodeKeepFirstKRows(NodeTemplate):

    ndname = _('Keep First K Rows')

    action = 'keep-first-k-rows'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeKeepFirstKRows(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['n-rows'] = 0

        self._add_output()
        self._add_input()
        self._add_n_rows()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['n-rows'] = args[0]

        widget = self.frame.contents[2].Widget
        widget.set_data(args[0])

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        n_rows = self.frame.data['n-rows']
        table = table.head(n_rows)

        self.frame.data['table'] = table

    def do_save(self) -> int:
        """"""
        return self.frame.data['n-rows']

    def do_restore(self,
                   value: int,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except:
            pass # TODO: show errors to user

    def _add_output(self) -> None:
        """"""
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
        label = NodeLabel(_('Table'))
        label.set_xalign(0.0)
        socket_type = NodeSocketType.INPUT
        content = self.frame.add_content(widget      = label,
                                         socket_type = socket_type,
                                         data_type   = DataFrame)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink

    def _add_n_rows(self) -> None:
        """"""
        def get_data() -> int:
            """"""
            return self.frame.data['n-rows']

        def set_data(value: int) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                self.frame.data['n-rows'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        spin = NodeSpinButton(title    = _('No. Rows'),
                              get_data = get_data,
                              set_data = set_data,
                              lower    = 0,
                              digits   = 0)
        socket_type = NodeSocketType.INPUT
        self.frame.add_content(widget      = spin,
                               socket_type = socket_type,
                               data_type   = int,
                               get_data    = get_data,
                               set_data    = set_data)



class NodeKeepLastKRows(NodeTemplate):

    ndname = _('Keep Last K Rows')

    action = 'keep-last-k-rows'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeKeepLastKRows(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['n-rows'] = 0

        self._add_output()
        self._add_input()
        self._add_n_rows()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['n-rows'] = args[0]

        widget = self.frame.contents[2].Widget
        widget.set_data(args[0])

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        n_rows = self.frame.data['n-rows']
        table = table.tail(n_rows)

        self.frame.data['table'] = table

    def do_save(self) -> int:
        """"""
        return self.frame.data['n-rows']

    def do_restore(self,
                   value: int,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except:
            pass # TODO: show errors to user

    def _add_output(self) -> None:
        """"""
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
        label = NodeLabel(_('Table'))
        label.set_xalign(0.0)
        socket_type = NodeSocketType.INPUT
        content = self.frame.add_content(widget      = label,
                                         socket_type = socket_type,
                                         data_type   = DataFrame)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink

    def _add_n_rows(self) -> None:
        """"""
        def get_data() -> int:
            """"""
            return self.frame.data['n-rows']

        def set_data(value: int) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                self.frame.data['n-rows'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        spin = NodeSpinButton(title    = _('No. Rows'),
                              get_data = get_data,
                              set_data = set_data,
                              lower    = 0,
                              digits   = 0)
        socket_type = NodeSocketType.INPUT
        self.frame.add_content(widget      = spin,
                               socket_type = socket_type,
                               data_type   = int,
                               get_data    = get_data,
                               set_data    = set_data)



class NodeKeepRangeOfRows(NodeTemplate):

    ndname = _('Keep Range of Rows')

    action = 'keep-range-of-rows'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeKeepRangeOfRows(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['offset'] = 0
        self.frame.data['n-rows'] = 0

        self._add_output()
        self._add_input()
        self._add_from_row()
        self._add_n_rows()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['offset'] = args[0]
        self.frame.data['n-rows'] = args[1]

        widget = self.frame.contents[2].Widget
        widget.set_data(args[0])

        widget = self.frame.contents[3].Widget
        widget.set_data(args[1])

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        offset = max(0, self.frame.data['offset'] - 1)
        n_rows = self.frame.data['n-rows']
        table = table.slice(offset, n_rows)

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'offset': self.frame.data['offset'],
            'n-rows': self.frame.data['n-rows'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['offset'],
                          value['n-rows'])
        except:
            pass # TODO: show errors to user

    def _add_output(self) -> None:
        """"""
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
        label = NodeLabel(_('Table'))
        label.set_xalign(0.0)
        socket_type = NodeSocketType.INPUT
        content = self.frame.add_content(widget      = label,
                                         socket_type = socket_type,
                                         data_type   = DataFrame)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink

    def _add_from_row(self) -> None:
        """"""
        def get_data() -> int:
            """"""
            return self.frame.data['offset']

        def set_data(value: int) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                self.frame.data['offset'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        spin = NodeSpinButton(title    = _('From Row'),
                              get_data = get_data,
                              set_data = set_data,
                              lower    = 0,
                              digits   = 0)
        socket_type = NodeSocketType.INPUT
        self.frame.add_content(widget      = spin,
                               socket_type = socket_type,
                               data_type   = int,
                               get_data    = get_data,
                               set_data    = set_data)

    def _add_n_rows(self) -> None:
        """"""
        def get_data() -> int:
            """"""
            return self.frame.data['n-rows']

        def set_data(value: int) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                self.frame.data['n-rows'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        spin = NodeSpinButton(title    = _('No. Rows'),
                              get_data = get_data,
                              set_data = set_data,
                              lower    = 0,
                              digits   = 0)
        socket_type = NodeSocketType.INPUT
        self.frame.add_content(widget      = spin,
                               socket_type = socket_type,
                               data_type   = int,
                               get_data    = get_data,
                               set_data    = set_data)



class NodeKeepEveryNthRows(NodeTemplate):

    ndname = _('Keep Every nth Rows')

    action = 'keep-every-nth-rows'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeKeepEveryNthRows(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['nth-row'] = 1
        self.frame.data['offset']  = 0

        self._add_output()
        self._add_input()
        self._add_nth_row()
        self._add_from_row()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['nth-row'] = args[0]
        self.frame.data['offset'] = args[1]

        widget = self.frame.contents[2].Widget
        widget.set_data(args[0])

        content = self.frame.contents[3]
        container = content.Widget
        box = container.get_first_child()
        value = box.get_last_child()
        value.set_label(str(args[1]))

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        nth_row = max(1, self.frame.data['nth-row'])
        offset = self.frame.data['offset']
        table = table.gather_every(nth_row, offset)

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'nth-row': self.frame.data['nth-row'],
            'offset':  self.frame.data['offset'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['nth-row'],
                          value['offset'])
        except:
            pass # TODO: show errors to user

    def _add_output(self) -> None:
        """"""
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
        label = NodeLabel(_('Table'))
        label.set_xalign(0.0)
        socket_type = NodeSocketType.INPUT
        content = self.frame.add_content(widget      = label,
                                         socket_type = socket_type,
                                         data_type   = DataFrame)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink

    def _add_nth_row(self) -> None:
        """"""
        def get_data() -> int:
            """"""
            return self.frame.data['nth-row']

        def set_data(value: int) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                self.frame.data['nth-row'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        spin = NodeSpinButton(title    = _('Nth Row'),
                              get_data = get_data,
                              set_data = set_data,
                              lower    = 0,
                              digits   = 0)
        socket_type = NodeSocketType.INPUT
        self.frame.add_content(widget      = spin,
                               socket_type = socket_type,
                               data_type   = int,
                               get_data    = get_data,
                               set_data    = set_data)

    def _add_from_row(self) -> None:
        """"""
        def get_data() -> int:
            """"""
            return self.frame.data['offset']

        def set_data(value: int) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                self.frame.data['offset'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        spin = NodeSpinButton(title    = _('From Row'),
                              get_data = get_data,
                              set_data = set_data,
                              lower    = 0,
                              digits   = 0)
        socket_type = NodeSocketType.INPUT
        self.frame.add_content(widget      = spin,
                               socket_type = socket_type,
                               data_type   = int,
                               get_data    = get_data,
                               set_data    = set_data)



class NodeKeepDuplicateRows(NodeTemplate):

    ndname = _('Keep Duplicate Rows')

    action = 'keep-duplicate-rows'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeKeepDuplicateRows(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['all-columns']     = []
        self.frame.data['columns']         = []
        self.frame.data['refresh-columns'] = False
        self.frame.data['column-expanded'] = False

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
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_columns()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_columns()

        if table.collect_schema().names():
            if columns := self.frame.data['columns']:
                from polars import struct
                table = table.filter(struct(columns).is_duplicated())

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
        except:
            pass # TODO: show errors to user

    def _add_output(self) -> None:
        """"""
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
        label = NodeLabel(_('Table'))
        label.set_xalign(0.0)
        socket_type = NodeSocketType.INPUT
        content = self.frame.add_content(widget      = label,
                                         socket_type = socket_type,
                                         data_type   = DataFrame)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink

    def _refresh_columns(self) -> None:
        """"""
        table = self.frame.data['table']

        # Filter unvalid columns from selection
        if isinstance(table, LazyFrame):
            table_columns = table.collect_schema().names()
        else:
            table_columns = table.columns

        if table_columns:
            if self.frame.data['columns']:
                columns = []
                for column in self.frame.data['columns']:
                    if column in table_columns:
                        columns.append(column)
                self.frame.data['columns'] = columns

        if self.frame.data['all-columns'] != table_columns:
            self.frame.data['refresh-columns'] = True

        self.frame.data['all-columns'] = table_columns

        if self.frame.data['refresh-columns']:
            if len(self.frame.contents) == 3:
                content = self.frame.contents[-1]
                self.frame.remove_content(content)
            if table_columns:
                self._add_columns()

        if self.frame.data['column-expanded']:
            if len(self.frame.contents) == 3:
                widget = self.frame.contents[-1].Widget
                widget.set_expanded(True)

        self.frame.data['refresh-columns'] = False

    def _add_columns(self) -> None:
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
            _take_snapshot(self, callback, value)

        group = NodeCheckGroup(get_data = get_data,
                               set_data = set_data,
                               options  = self.frame.data['all-columns'])
        expander = Gtk.Expander(label = _('Based On'),
                                child = group)
        self.frame.add_content(expander, None)

        def on_expanded(widget:     Gtk.Widget,
                        param_spec: GObject.ParamSpec,
                        ) ->        None:
            """"""
            self.frame.data['column-expanded'] = expander.get_expanded()

        expander.connect('notify::expanded', on_expanded)



class NodeRemoveFirstKRows(NodeTemplate):

    ndname = _('Remove First K Rows')

    action = 'remove-first-k-rows'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeRemoveFirstKRows(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['n-rows'] = 0

        self._add_output()
        self._add_input()
        self._add_n_rows()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['n-rows'] = args[0]

        widget = self.frame.contents[2].Widget
        widget.set_data(args[0])

        self.frame.data['refresh-columns'] = True

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        n_rows = self.frame.data['n-rows']
        table = table.tail(-n_rows)

        self.frame.data['table'] = table

    def do_save(self) -> int:
        """"""
        return self.frame.data['n-rows']

    def do_restore(self,
                   value: int,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except:
            pass # TODO: show errors to user

    def _add_output(self) -> None:
        """"""
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
        label = NodeLabel(_('Table'))
        label.set_xalign(0.0)
        socket_type = NodeSocketType.INPUT
        content = self.frame.add_content(widget      = label,
                                         socket_type = socket_type,
                                         data_type   = DataFrame)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink

    def _add_n_rows(self) -> None:
        """"""
        def get_data() -> int:
            """"""
            return self.frame.data['n-rows']

        def set_data(value: int) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                self.frame.data['n-rows'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        spin = NodeSpinButton(title    = _('No. Rows'),
                              get_data = get_data,
                              set_data = set_data,
                              lower    = 0,
                              digits   = 0)
        socket_type = NodeSocketType.INPUT
        self.frame.add_content(widget      = spin,
                               socket_type = socket_type,
                               data_type   = int,
                               get_data    = get_data,
                               set_data    = set_data)



class NodeRemoveLastKRows(NodeTemplate):

    ndname = _('Remove Last K Rows')

    action = 'remove-last-k-rows'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeRemoveLastKRows(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['n-rows'] = 0

        self._add_output()
        self._add_input()
        self._add_n_rows()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['n-rows'] = args[0]

        widget = self.frame.contents[2].Widget
        widget.set_data(args[0])

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        n_rows = self.frame.data['n-rows']
        table = table.head(-n_rows)

        self.frame.data['table'] = table

    def do_save(self) -> int:
        """"""
        return self.frame.data['n-rows']

    def do_restore(self,
                   value: int,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except:
            pass # TODO: show errors to user

    def _add_output(self) -> None:
        """"""
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
        label = NodeLabel(_('Table'))
        label.set_xalign(0.0)
        socket_type = NodeSocketType.INPUT
        content = self.frame.add_content(widget      = label,
                                         socket_type = socket_type,
                                         data_type   = DataFrame)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink

    def _add_n_rows(self) -> None:
        """"""
        def get_data() -> int:
            """"""
            return self.frame.data['n-rows']

        def set_data(value: int) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                self.frame.data['n-rows'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        spin = NodeSpinButton(title    = _('No. Rows'),
                              get_data = get_data,
                              set_data = set_data,
                              lower    = 0,
                              digits   = 0)
        socket_type = NodeSocketType.INPUT
        self.frame.add_content(widget      = spin,
                               socket_type = socket_type,
                               data_type   = int,
                               get_data    = get_data,
                               set_data    = set_data)



class NodeRemoveRangeOfRows(NodeTemplate):

    ndname = _('Remove Range of Rows')

    action = 'remove-range-of-rows'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeRemoveRangeOfRows(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['offset'] = 0
        self.frame.data['n-rows'] = 0

        self._add_output()
        self._add_input()
        self._add_from_row()
        self._add_n_rows()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['offset'] = args[0]
        self.frame.data['n-rows'] = args[1]

        widget = self.frame.contents[2].Widget
        widget.set_data(args[0])

        widget = self.frame.contents[3].Widget
        widget.set_data(args[1])

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        from polars import concat
        offset = max(0, self.frame.data['offset'] - 1)
        n_rows = self.frame.data['n-rows']
        table = concat([table.head(offset),
                        table.slice(offset + n_rows)])

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'offset': self.frame.data['offset'],
            'n-rows': self.frame.data['n-rows'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['offset'],
                          value['n-rows'])
        except:
            pass # TODO: show errors to user

    def _add_output(self) -> None:
        """"""
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
        label = NodeLabel(_('Table'))
        label.set_xalign(0.0)
        socket_type = NodeSocketType.INPUT
        content = self.frame.add_content(widget      = label,
                                         socket_type = socket_type,
                                         data_type   = DataFrame)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink

    def _add_from_row(self) -> None:
        """"""
        def get_data() -> int:
            """"""
            return self.frame.data['offset']

        def set_data(value: int) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                self.frame.data['offset'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        spin = NodeSpinButton(title    = _('From Row'),
                              get_data = get_data,
                              set_data = set_data,
                              lower    = 0,
                              digits   = 0)
        socket_type = NodeSocketType.INPUT
        self.frame.add_content(widget      = spin,
                               socket_type = socket_type,
                               data_type   = int,
                               get_data    = get_data,
                               set_data    = set_data)

    def _add_n_rows(self) -> None:
        """"""
        def get_data() -> int:
            """"""
            return self.frame.data['n-rows']

        def set_data(value: int) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                self.frame.data['n-rows'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        spin = NodeSpinButton(title    = _('No. Rows'),
                              get_data = get_data,
                              set_data = set_data,
                              lower    = 0,
                              digits   = 0)
        socket_type = NodeSocketType.INPUT
        self.frame.add_content(widget      = spin,
                               socket_type = socket_type,
                               data_type   = int,
                               get_data    = get_data,
                               set_data    = set_data)



class NodeRemoveDuplicateRows(NodeTemplate):

    ndname = _('Remove Duplicate Rows')

    action = 'remove-duplicate-rows'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeRemoveDuplicateRows(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['keep-rows']       = _('Any')
        self.frame.data['keep-order']      = False
        self.frame.data['all-columns']     = []
        self.frame.data['columns']         = []
        self.frame.data['refresh-columns'] = False
        self.frame.data['column-expanded'] = False

        self._add_output()
        self._add_input()
        self._add_keep_rows()
        self._add_keep_order()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['keep-rows']  = args[0]
        self.frame.data['keep-order'] = args[1]
        self.frame.data['columns']    = args[2]

        widget = self.frame.contents[2].Widget
        widget.set_data(args[0])

        widget = self.frame.contents[3].Widget
        widget.set_data(args[1])

        self.frame.data['refresh-columns'] = True

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_columns()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_columns()

        if table.collect_schema().names():
            if columns := self.frame.data['columns']:
                keep = self.frame.data['keep-rows'].lower()
                order = self.frame.data['keep-order']
                table = table.unique(columns,
                                     keep           = keep,
                                     maintain_order = order)

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'keep-rows':  self.frame.data['keep-rows'],
            'keep-order': self.frame.data['keep-order'],
            'columns':    deepcopy(self.frame.data['columns']),
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['keep-rows'],
                          value['keep-order'],
                          value['columns'])
        except:
            pass # TODO: show errors to user

    def _add_output(self) -> None:
        """"""
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
        label = NodeLabel(_('Table'))
        label.set_xalign(0.0)
        socket_type = NodeSocketType.INPUT
        content = self.frame.add_content(widget      = label,
                                         socket_type = socket_type,
                                         data_type   = DataFrame)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink

    def _add_keep_rows(self) -> None:
        """"""
        def get_data() -> str:
            """"""
            return self.frame.data['keep-rows']

        def set_data(value: str) -> None:
            """"""
            def callback(value: str) -> None:
                """"""
                self.frame.data['keep-rows'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        options = {
            _('Any'):   _('Any'),
            _('None'):  _('None'),
            _('First'): _('First'),
            _('Last'):  _('Last'),
        }
        combo = NodeComboButton(title    = _('Rows to Keep'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = options)
        self.frame.add_content(widget    = combo,
                               get_data  = get_data,
                               set_data  = set_data)

    def _add_keep_order(self) -> None:
        """"""
        def get_data() -> bool:
            """"""
            return self.frame.data['keep-order']

        def set_data(value: bool) -> None:
            """"""
            def callback(value: bool) -> None:
                """"""
                self.frame.data['keep-order'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        check = NodeCheckButton(title    = _('Maintain Order'),
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

            label = NodeLabel(_('Maintain Order'), linked = True)
            label.insert_after(content.Container, content.Socket)

            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.data['orig-keep-order'] = self.frame.data['keep-order']

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            self.frame.data['keep-order'] = self.frame.data['orig-keep-order']

            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink

    def _refresh_columns(self) -> None:
        """"""
        table = self.frame.data['table']

        # Filter unvalid columns from selection
        if isinstance(table, LazyFrame):
            table_columns = table.collect_schema().names()
        else:
            table_columns = table.columns

        if table_columns:
            if self.frame.data['columns']:
                columns = []
                for column in self.frame.data['columns']:
                    if column in table_columns:
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
                self._add_columns()

        if self.frame.data['column-expanded']:
            if len(self.frame.contents) == 5:
                widget = self.frame.contents[-1].Widget
                widget.set_expanded(True)

        self.frame.data['refresh-columns'] = False

    def _add_columns(self) -> None:
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
            _take_snapshot(self, callback, value)

        group = NodeCheckGroup(get_data = get_data,
                               set_data = set_data,
                               options  = self.frame.data['all-columns'])
        expander = Gtk.Expander(label = _('Based On'),
                                child = group)
        self.frame.add_content(expander, None)

        def on_expanded(widget:     Gtk.Widget,
                        param_spec: GObject.ParamSpec,
                        ) ->        None:
            """"""
            self.frame.data['column-expanded'] = expander.get_expanded()

        expander.connect('notify::expanded', on_expanded)



_registered_nodes = [
    NodeBoolean(),
    NodeDecimal(),
    NodeInteger(),
    NodeString(),

    NodeReadFile(),
    NodeSheet(),
    NodeViewer(),

    NodeChooseColumns(),
    NodeRemoveColumns(),

    NodeKeepTopKRows(),
    NodeKeepBottomKRows(),
    NodeKeepFirstKRows(),
    NodeKeepLastKRows(),
    NodeKeepRangeOfRows(),
    NodeKeepEveryNthRows(),
    NodeKeepDuplicateRows(),

    NodeRemoveFirstKRows(),
    NodeRemoveLastKRows(),
    NodeRemoveRangeOfRows(),
    NodeRemoveDuplicateRows(),
]


def create_new_node(name: str,
                    x:    int,
                    y:    int,
                    ) ->  NodeFrame:
    """"""
    for node in _registered_nodes:
        if name in {node.ndname, node.action}:
            return node.new(x, y)
    return NodeFrame(name, x, y)
