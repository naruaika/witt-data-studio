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
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Pango
from polars import DataFrame
from polars import LazyFrame
from polars import Series
from polars import DataType
from polars import Expr
from typing import Any
import gc

from ..core.utils import generate_uuid
from ..core.utils import isiterable
from ..core.utils import unique_name

from .content import NodeContent
from .data_type import Sheet
from .frame import NodeFrame
from .frame import NodeFrameType
from .socket import NodeSocket
from .socket import NodeSocketType
from .widget import NodeCheckButton
from .widget import NodeCheckGroup
from .widget import NodeComboButton
from .widget import NodeEntry
from .widget import NodeFileChooser
from .widget import NodeFormulaEditor
from .widget import NodeFilterBuilder
from .widget import NodeLabel
from .widget import NodeListEntry
from .widget import NodeListItem
from .widget import NodeSpinButton

def _iscompatible(pair_socket:  NodeSocket,
                  self_content: NodeContent,
                  ) ->          bool:
    """"""
    self_socket = self_content.Socket

    if not (pair_socket.data_type and self_socket.data_type):
        compatible = True
    else:
        pair_types = set(pair_socket.data_type) if isiterable(pair_socket.data_type) \
                                                else {pair_socket.data_type}
        self_types = set(self_socket.data_type) if isiterable(self_socket.data_type) \
                                                else {self_socket.data_type}
        compatible = not pair_types.isdisjoint(self_types)

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


def _serialize_data(obj: Any) -> Any:
    """"""
    if isinstance(obj, datetime):
        return {
            '_type': 'datetime',
            'value': obj.isoformat()
        }

    if isinstance(obj, date):
        return {
            '_type': 'date',
            'value': obj.isoformat()
        }

    if isinstance(obj, time):
        return {
            '_type': 'time',
            'value': obj.isoformat()
        }

    if isinstance(obj, dict):
        return {
            key: _serialize_data(value)
                 for key, value in obj.items()
        }

    if isiterable(obj):
        return [_serialize_data(item) for item in obj]

    return obj


def _deserialize_data(obj) -> Any:
    """"""
    if isinstance(obj, dict) and '_type' in obj:
        _type = obj['_type']
        value = obj['value']

        if _type == 'datetime':
            return datetime.fromisoformat(value)

        if _type == 'date':
            return date.fromisoformat(value)

        if _type == 'time':
            return time.fromisoformat(value)

        return obj

    if isinstance(obj, dict):
        return {
            key: _deserialize_data(value)
                 for key, value in obj.items()
        }

    if isinstance(obj, list):
        return [_deserialize_data(item) for item in obj]

    return obj


def _take_snapshot(node:     'NodeTemplate',
                   callback: 'callable',
                   *args:    'list',
                   **kwargs: 'dict',
                   ) ->      'None':
    """"""
    from .action import ActionEditNode

    old_data = node.do_save()
    callback(*args, **kwargs)
    new_data = node.do_save()

    editor = node.frame.get_editor()
    window = editor.get_window()

    values = (old_data, new_data)
    action = ActionEditNode(editor, node.frame, values)

    window.do(action, add_only = True)



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
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

    def _add_output(self) -> None:
        """"""
        def get_data() -> bool:
            """"""
            return self.frame.data['value']

        def set_data(value: bool) -> None:
            """"""
            _take_snapshot(self, self.set_data, value)

        check = NodeCheckButton(title    = _('Boolean'),
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
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

    def _add_output(self) -> None:
        """"""
        def get_data() -> float:
            """"""
            return self.frame.data['value']

        def set_data(value: float) -> None:
            """"""
            _take_snapshot(self, self.set_data, value)

        spin = NodeEntry(title    = _('Decimal'),
                         get_data = get_data,
                         set_data = set_data)
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
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

    def _add_output(self) -> None:
        """"""
        def get_data() -> int:
            """"""
            return self.frame.data['value']

        def set_data(value: int) -> None:
            """"""
            _take_snapshot(self, self.set_data, value)

        spin = NodeSpinButton(title    = _('Integer'),
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
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

    def _add_output(self) -> None:
        """"""
        def get_data() -> str:
            """"""
            return self.frame.data['value']

        def set_data(value: str) -> None:
            """"""
            _take_snapshot(self, self.set_data, value)

        entry = NodeEntry(title    = _('String'),
                          get_data = get_data,
                          set_data = set_data)
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

        self.frame.node_type  = NodeFrameType.SOURCE
        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['file-path']        = ''
        self.frame.data['all-columns']      = []
        self.frame.data['kwargs']           = {}
        self.frame.data['refresh-columns']  = False
        self.frame.data['column-expanded']  = False
        self.frame.data['limiter-expanded'] = False

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

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        file_path = self.frame.data.get('file-path')

        if not file_path:
            return

        kwargs = self.frame.data['kwargs']
        kwargs = deepcopy(kwargs)

        # Do not include the columns when taking a sample
        del kwargs['columns']

        has_error = False
        self.frame.ErrorButton.set_visible(False)

        # Read file at the given path with pre-processed args
        from polars import LazyFrame
        from ..core.file_manager import FileManager
        try:
            result = FileManager.read_file(file_path, **kwargs)
            if isinstance(result, LazyFrame):
                result.head(1_000).collect()
        except FileNotFoundError:
            self.frame.ErrorButton.set_tooltip_text(f'{_('File not found')}: {file_path}')
            self.frame.ErrorButton.set_visible(True)
            return
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
            except Exception as e:
                self.frame.ErrorButton.set_tooltip_text(str(e))
                self.frame.ErrorButton.set_visible(True)

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
                has_error = False
            except Exception as e:
                self.frame.ErrorButton.set_tooltip_text(str(e))
                self.frame.ErrorButton.set_visible(True)

        if has_error:
            result = DataFrame()

#       # Post-process the resulting data
#       from fastexcel import ExcelReader
#       if isinstance(result, ExcelReader):
#           pass

        table_columns = result.collect_schema().names()
        self.frame.data['all-columns'] = table_columns

        # TODO: if the workflow is run on schedule and the source
        # seems has changed, stop the process and notify the user

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

        if self.frame.data['column-expanded']:
            widget = self.frame.contents[-1].Widget
            widget.set_expanded(True)

        self.frame.data['refresh-columns'] = False

        self.frame.data['table'] = result

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
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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

        if self.frame.data['limiter-expanded']:
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
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        from ..file_import_csv_view import SEPARATOR_OPTS
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
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        from ..file_import_csv_view import QUOTE_CHAR_OPTS
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
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        from ..file_import_csv_view import DECIMAL_COMMA_OPTS
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

            label = NodeLabel(_('No. Rows'), can_link = True)
            label.insert_after(content.Container, content.Socket)

            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.data['bk.n_rows'] = content.get_data()

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            if 'bk.n_rows' in self.frame.data:
                content.set_data(self.frame.data['bk.n_rows'])

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

            label = NodeLabel(_('From Row'), can_link = True)
            label.insert_after(content.Container, content.Socket)

            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.data['bk.skip_rows'] = content.get_data()

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            if 'bk.skip_rows' in self.frame.data:
                content.set_data(self.frame.data['bk.skip_rows'])

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

            label = NodeLabel(_('First Row as Header'), can_link = True)
            label.insert_after(content.Container, content.Socket)

            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.data['bk.has_header'] = content.get_data()

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            if 'bk.has_header' in self.frame.data:
                content.set_data(self.frame.data['bk.has_header'])

            self.frame.data['kwargs']['columns'] = []

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
        self.frame.add_content(expander)

        def on_expanded(widget:     Gtk.Widget,
                        param_spec: GObject.ParamSpec,
                        ) ->        None:
            """"""
            self.frame.data['column-expanded'] = expander.get_expanded()

        expander.connect('notify::expanded', on_expanded)

        if self.frame.data['column-expanded']:
            expander.set_expanded(True)



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
        value.tables = {}

        for self_content in self.frame.contents[1:-1]:
            box = self_content.Widget
            label = box.get_first_child()
            title = label.get_label()
            if title not in self.frame.data:
                continue

            self_socket = self_content.Socket
            if links := self_socket.links:
                psocket = links[0].in_socket
                pcontent = psocket.Content
                table = pcontent.get_data()
                coordinate = self.frame.data[title]
                value.tables[title] = (coordinate, table)

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
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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

        widget = NodeLabel(_('Sheet'))
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
                         content: NodeContent,
                         ) ->     str:
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
            widget = self_content.Widget
            label = widget.get_first_child()

            old_title = label.get_label()
            new_title = old_title

            # Auto-generate the socket label if needed
            if not self_content.is_freezing:
                titles = [
                    content.Widget.get_first_child().get_label()
                    for content in self.frame.contents[1:-1]
                    if content != self_content
                ]
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

    PRIMITIVE_TYPES = {bool, float, int, str, list, dict, tuple}

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeViewer(x, y)

        self.frame.node_type  = NodeFrameType.TARGET
        self.frame.is_active  = self.is_active
        self.frame.set_active = self.set_active
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['is-active']      = False
        self.frame.data['replace-titles'] = {}

        self._add_input()

        self._setup_uinterfaces()

        return self.frame

    def _setup_uinterfaces(self) -> None:
        """"""
        self.frame.ActiveToggle.set_visible(True)

        def on_activated(button: Gtk.Button) -> None:
            editor = self.frame.get_editor()
            editor.select_viewer(self.frame)

        self.frame.ActiveToggle.connect('clicked', on_activated)

    def is_active(self) -> bool:
        """"""
        return self.frame.data['is-active']

    def set_active(self,
                   active: bool,
                   ) ->    None:
        """"""
        self.frame.data['is-active'] = active

        if active:
            self.frame.ActiveToggle.set_icon_name('view-reveal-symbolic')
            self.frame.ActiveToggle.remove_css_class('dimmed')
        else:
            self.frame.ActiveToggle.set_icon_name('view-conceal-symbolic')
            self.frame.ActiveToggle.add_css_class('dimmed')

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

            elif pair_socket.data_type in {DataFrame, LazyFrame, Series}:
                if isinstance(value, LazyFrame):
                    try:
                        value = value.collect()
                    except Exception as e:
                        value = e
                label.set_label(str(value))

            elif value is None:
                label.set_label(f'[{_('None')}]')

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
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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

            label = self_content.Widget
            title = label.get_label()

            if pair_socket.data_type in self.SUPPORTED_VIEWS:
                if not self_content.is_freezing:
                    # Auto-generate the socket label if needed
                    titles = [
                        content.Widget.get_label()
                        for content in self.frame.contents[:-1]
                        if content != self_content
                    ]
                    title = pair_socket.data_type.__name__
                    title = unique_name(title, titles)
                    label.set_label(title)

            elif pair_socket.data_type in self.PRIMITIVE_TYPES:
                label.set_ellipsize(Pango.EllipsizeMode.NONE)

                if pair_socket.data_type == str:
                    label.set_wrap(True)
                    label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)

            elif pair_socket.data_type in {DataFrame, LazyFrame, Series}:
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

            if self.is_active():
                if pair_socket.data_type == Sheet:
                    args = (title, pair_socket, self_content)
                    GLib.idle_add(self.add_sheet_editor, *args)

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

    def add_sheet_editor(self,
                         title:        str,
                         pair_socket:  NodeSocket,
                         self_content: NodeContent,
                         ) ->          bool:
        """"""
        from ..sheet.editor import SheetEditor

        if not self.is_active():
            return Gdk.EVENT_PROPAGATE

        if window := self.frame.get_root():
            frame = pair_socket.Frame
            sheet = pair_socket.Content.get_data()
            editor = SheetEditor(title,
                                 sheet.tables,
                                 sheet.sparse,
                                 node = frame)
            self_content.Page = window.add_new_editor(editor)
            return Gdk.EVENT_PROPAGATE

        return Gdk.EVENT_STOP



class NodeCustomFormula(NodeTemplate):

    ndname = _('Custom Formula')

    action = 'custom-formula'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCustomFormula(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['formula'] = 'value'

        self._add_output()
        self._add_input()
        self._add_formula()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['formula'] = args[0]

        widget = self.frame.contents[2].Widget
        widget.set_data(args[0])

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        in_content = self.frame.contents[1]

        out_content = self.frame.contents[0]
        out_socket = out_content.Socket

        value = None
        self.frame.data['value'] = value
        out_socket.data_type = None

        if links := in_content.Socket.links:
            pair_content = links[0].in_socket.Content
            value = pair_content.get_data()
            out_socket.data_type = type(value)

        if formula := self.frame.data['formula']:
            from ..core.formula_evaluator import Evaluator
            try:
                variables = {'value': value}
                value = Evaluator(variables).evaluate(formula)
                out_socket.data_type = type(value)
            except Exception as e:
                self.frame.ErrorButton.set_tooltip_text(str(e))
                self.frame.ErrorButton.set_visible(True)
            else:
                self.frame.ErrorButton.set_visible(False)

        # Make compatible with existing nodes
        if out_socket.data_type == LazyFrame:
            out_socket.data_type = DataFrame

        self.frame.data['value'] = value

    def do_save(self) -> str:
        """"""
        return self.frame.data['formula']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

    def _add_output(self) -> None:
        """"""
        self.frame.data['value'] = None

        def get_data() -> Any:
            """"""
            return self.frame.data['value']

        def set_data(value: Any) -> None:
            """"""
            self.frame.data['value'] = value
            self.frame.do_execute(backward = False)

        widget = NodeLabel(_('Value'))
        socket_type = NodeSocketType.OUTPUT
        self.frame.add_content(widget      = widget,
                               socket_type = socket_type,
                               get_data    = get_data,
                               set_data    = set_data)

    def _add_input(self) -> None:
        """"""
        label = NodeLabel(_('Value'), can_link = True)
        socket_type = NodeSocketType.INPUT
        content = self.frame.add_content(widget      = label,
                                         socket_type = socket_type)

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

    def _add_formula(self) -> None:
        """"""
        def get_data() -> str:
            """"""
            return self.frame.data['formula']

        def set_data(value: str) -> None:
            """"""
            def callback(value: str) -> None:
                """"""
                self.frame.data['formula'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        widget = NodeFormulaEditor(get_data = get_data,
                                   set_data = set_data)
        self.frame.add_content(widget   = widget,
                               get_data = get_data,
                               set_data = set_data)



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
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
        self.frame.add_content(expander)

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

        table_columns = self.frame.data['all-columns']

        if table_columns:
            import polars.selectors as cs
            columns = self.frame.data['columns']
            table = table.select(cs.exclude(columns))

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
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
        self.frame.add_content(expander)

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

        if self.frame.data['all-columns']:
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
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
        self.frame.add_content(expander)

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

        if self.frame.data['all-columns']:
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
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
        self.frame.add_content(expander)

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
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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

        if self.frame.data['all-columns']:
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
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
        self.frame.add_content(expander)

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
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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

        self.frame.data['all-keeps']       = {'any':   _('Any'),
                                              'none':  _('None'),
                                              'first': _('First'),
                                              'last':  _('Last')}
        self.frame.data['keep-rows']       = 'any'
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

        options = self.frame.data['all-keeps']
        option = list(options.keys())[0]
        if args[0] in options:
            option = options[args[0]]
        widget = self.frame.contents[2].Widget
        widget.set_data(option)

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

        if self.frame.data['all-columns']:
            if columns := self.frame.data['columns']:
                keep = self.frame.data['keep-rows']
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
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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

        combo = NodeComboButton(title    = _('Rows to Keep'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['all-keeps'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

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

            label = NodeLabel(_('Maintain Order'), can_link = True)
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
        self.frame.add_content(expander)

        def on_expanded(widget:     Gtk.Widget,
                        param_spec: GObject.ParamSpec,
                        ) ->        None:
            """"""
            self.frame.data['column-expanded'] = expander.get_expanded()

        expander.connect('notify::expanded', on_expanded)



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
        self.frame.data['level-expanded'] = False

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
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_selector()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

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
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            self.frame.data['level-expanded'] = True

        if self.frame.data['level-expanded']:
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
            _take_snapshot(self, callback, value)

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
            self.frame.data['level-expanded'] = expander.get_expanded()

        expander.connect('notify::expanded', on_expanded)



class NodeFilterRows(NodeTemplate):

    ndname = _('Filter Rows')

    action = 'filter-rows'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeFilterRows(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['all-columns']     = []
        self.frame.data['clauses']         = []
        self.frame.data['refresh-clauses'] = True
        self.frame.data['clause-expanded'] = False

        self._add_output()
        self._add_input()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        if isinstance(args, tuple):
            args = list(args)
        self.frame.data['clauses'] = args
        self.frame.data['refresh-clauses'] = True
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

        if self.frame.data['all-columns']:
            if clauses := self.frame.data['clauses']:
                table = self._build_filter_expr(table, clauses)

        self.frame.data['table'] = table

    def _build_filter_expr(self,
                           table:   LazyFrame,
                           clauses: list,
                           ) ->     LazyFrame:
        """"""
        if not clauses:
            return table

        expr = None

        for clause in clauses:
            operator = clause[0]

            _expr = self._build_expression(table, clause)

            if expr is None:
                expr = _expr
                continue
            if operator == 'and':
                expr = expr & _expr
                continue
            if operator == 'or':
                expr = expr | _expr
                continue

            raise ValueError()

        return table.filter(expr)

    def _build_expression(self,
                          table:  LazyFrame,
                          clause: list,
                          ) ->    None:
        """"""
        from polars import col

        _, column, operator, *values = clause

        expr = col(column)

        if operator == 'is-null':
            return expr.is_null()

        if operator == 'is-not-null':
            return expr.is_not_null()

        if operator == 'equals':
            return expr == values[0]

        if operator == 'does-not-equal':
            return expr != values[0]

        if operator == 'begins-with':
            return expr.str.starts_with(values[0])

        if operator == 'does-not-begin-with':
            return ~expr.str.starts_with(values[0])

        if operator == 'ends-with':
            return expr.str.ends_with(values[0])

        if operator == 'does-not-end-with':
            return expr.str.ends_with(values[0]).not_()

        if operator == 'contains':
            return expr.str.contains(values[0], literal = True)

        if operator == 'does-not-contain':
            return ~expr.str.contains(values[0], literal = True)

        if operator in {'is-greater-than',
                        'is-after'}:
            return expr > values[0]

        if operator in {'is-greater-than-or-equal-to',
                        'is-after-or-equal-to'}:
            return expr >= values[0]

        if operator in {'is-less-than',
                        'is-before'}:
            return expr < values[0]

        if operator in {'is-less-than-or-equal-to',
                        'is-before-or-equal-to'}:
            return expr <= values[0]

        if operator == 'is-between':
            return expr.is_between(values[0], values[1])

        if operator == 'is-not-between':
            return ~expr.is_between(values[0], values[1])

        if operator == 'above-average':
            return expr > expr.mean()

        if operator == 'below-average':
            return expr < expr.mean()

        if operator == 'is-earliest':
            return expr == expr.min()

        if operator == 'is-latest':
            return expr == expr.max()

        if operator == 'is-not-earliest':
            return expr != expr.min()

        if operator == 'is-not-latest':
            return expr != expr.max()

        now = datetime.now()

        if operator == 'is-in-the-next':
            amount, unit = values
            start, end = self._relative_period_bounds(now, amount, unit, 'next')
            return expr.is_between(start, end)

        if operator == 'is-in-the-previous':
            amount, unit = values
            start, end = self._relative_period_bounds(now, amount, unit, 'previous')
            return expr.is_between(start, end)

        if operator == 'is-in-year':
            start, end = self._year_bounds(now, values[0])
            return expr.is_between(start, end)

        if operator == 'is-in-quarter':
            value = values[0]

            if value.startswith('quarter-'):
                q = int(value.split('-')[1])
                return ((expr.dt.month() - 1) // 3 + 1) == q

            start, end = self._quarter_bounds(now, value)
            return expr.is_between(start, end)

        if operator == 'is-in-month':
            value = values[0]

            if value in {'last-month',
                         'this-month',
                         'next-month'}:
                start, end = self._month_bounds(now, value)
                return expr.is_between(start, end)

            mapping = {
                'january':   1,
                'february':  2,
                'march':     3,
                'april':     4,
                'may':       5,
                'june':      6,
                'july':      7,
                'august':    8,
                'september': 9,
                'october':   10,
                'november':  11,
                'december':  12,
            }

            if value in mapping:
                return expr.dt.month() == mapping[value]

        if operator == 'is-in-week':
            start, end = self._week_bounds(now, values[0])
            return expr.is_between(start, end)

        if operator == 'is-in-day':
            start, end = self._day_bounds(now, values[0])
            return expr.is_between(start, end)

        raise ValueError()

    def _relative_period_bounds(self,
                                now:       datetime,
                                amount:    int,
                                unit:      str,
                                direction: str,
                                ) ->       timedelta:
        """"""
        if unit == 'years':
            year = now.year

            if direction == 'next':
                start_year = year + 1
                end_year   = year + amount
            else:
                start_year = year - amount
                end_year   = year - 1

            start = datetime(start_year, 1, 1)
            end   = datetime(end_year, 12, 31, 23, 59, 59, 999999)
            return start, end

        if unit == 'quarters':
            quarter = (now.month - 1) // 3 + 1

            if direction == 'next':
                q_start = quarter + 1
                q_end   = quarter + amount
            else:
                q_start = quarter - amount
                q_end   = quarter - 1

            start_year = now.year
            while q_start <= 0:
                q_start += 4
                start_year -= 1
            while q_start > 4:
                q_start -= 4
                start_year += 1

            end_year = start_year
            while q_end <= 0:
                q_end += 4
                end_year -= 1
            while q_end > 4:
                q_end -= 4
                end_year += 1

            start_month = (q_start - 1) * 3 + 1
            end_month   = (q_end   - 1) * 3 + 3

            from calendar import monthrange

            end_day = monthrange(end_year, end_month)[1]
            start   = datetime(start_year, start_month, 1)
            end     = datetime(end_year, end_month, end_day, 23, 59, 59, 999999)
            return start, end

        if unit == 'months':
            if direction == 'next':
                start_month_offset = 1
            else:
                start_month_offset = -amount

            if direction == 'next':
                start_offset = 1
                end_offset   = amount
            else:
                start_offset = -amount
                end_offset   = -1

            def add_months(dt:     datetime,
                           offset: int,
                           ) ->    datetime:
                """"""
                year = dt.year + (dt.month - 1 + offset) // 12
                month = (dt.month - 1 + offset) % 12 + 1
                return datetime(year, month, 1)

            from calendar import monthrange

            end_month = add_months(now.replace(day = 1), end_offset)
            end_day   = monthrange(end_month.year, end_month.month)[1]
            start     = add_months(now.replace(day = 1), start_offset)
            end       = datetime(end_month.year, end_month.month, end_day, 23, 59, 59, 999999)
            return start, end

        if unit == 'weeks':
            current_week_start = now - timedelta(days = now.weekday())

            if direction == 'next':
                start = current_week_start + timedelta(weeks = 1)
                end   = current_week_start + timedelta(weeks = amount)
            else:
                start = current_week_start - timedelta(weeks = amount)
                end   = current_week_start - timedelta(weeks = 1)

            start = start.replace(hour        = 0,
                                  minute      = 0,
                                  second      = 0,
                                  microsecond = 0)
            end = end + timedelta(days         = 6,
                                  hours        = 23,
                                  minutes      = 59,
                                  seconds      = 59,
                                  microseconds = 999999)
            return start, end

        mapping = {
            'days':    timedelta(days    = amount),
            'hours':   timedelta(hours   = amount),
            'minutes': timedelta(minutes = amount),
            'seconds': timedelta(seconds = amount),
        }

        if unit not in mapping:
            unit = 'days'
        delta = mapping[unit]

        if direction == 'next':
            return now, now + delta
        else:
            return now - delta, now

    def _year_bounds(self,
                     now:   datetime,
                     value: str,
                     ) ->   tuple:
        """"""
        if value == 'this-year':
            return (self._start_of_year(now), self._end_of_year(now))

        if value == 'last-year':
            dt = now.replace(year = now.year - 1)
            return (self._start_of_year(dt), self._end_of_year(dt))

        if value == 'next-year':
            dt = now.replace(year = now.year + 1)
            return (self._start_of_year(dt), self._end_of_year(dt))

        if value == 'year-to-date':
            return (self._start_of_year(now), now)

    def _quarter_bounds(self,
                        now:   datetime,
                        value: str,
                        ) ->   tuple:
        """"""
        current = (now.month - 1) // 3 + 1

        def bounds(year:    int,
                   quarter: int,
                   ) ->     tuple:
            """"""
            start_month = (quarter - 1) * 3 + 1
            start = datetime(year, start_month, 1)

            if quarter == 4:
                end = datetime(year, 12, 31, 23, 59, 59, 999999)
            else:
                end = datetime(year, start_month + 3, 1) - timedelta(microseconds = 1)

            return start, end

        if value == 'this-quarter':
            return bounds(now.year, current)

        if value == 'last-quarter':
            quarter = current - 1 or 4
            year = now.year - 1 if current == 1 else now.year
            return bounds(year, quarter)

        if value == 'next-quarter':
            quarter = current + 1 if current < 4 else 1
            year = now.year + 1 if current == 4 else now.year
            return bounds(year, quarter)

    def _month_bounds(self,
                      now:   datetime,
                      value: str,
                      ) ->   tuple:
        """"""
        dt = now
        if value == 'last-month':
            dt = (now.replace(day = 1) - timedelta(days = 1))
        if value == 'next-month':
            dt = (now.replace(day = 28) + timedelta(days = 4))
            dt = dt.replace(day = 1)
        return self._start_of_month(dt), self._end_of_month(dt)

    def _week_bounds(self,
                     now:   datetime,
                     value: str,
                     ) ->   tuple:
        """"""
        dt = now
        if value == 'last-week':
            dt = now - timedelta(weeks = 1)
        if value == 'next-week':
            dt = now + timedelta(weeks = 1)
        return self._start_of_week(dt), self._end_of_week(dt)

    def _day_bounds(self,
                    now:   datetime,
                    value: str,
                    ) ->   tuple:
        """"""
        dt = now
        if value == 'yesterday':
            dt = now - timedelta(days = 1)
        if value == 'tomorrow':
            dt = now + timedelta(days = 1)
        start = datetime(dt.year, dt.month, dt.day)
        end = start + timedelta(days = 1) - timedelta(microseconds = 1)
        return start, end

    def _start_of_year(self,
                       dt:  datetime,
                       ) -> datetime:
        """"""
        return datetime(dt.year, 1, 1)

    def _end_of_year(self,
                     dt:  datetime,
                     ) -> datetime:
        """"""
        return datetime(dt.year, 12, 31, 23, 59, 59, 999999)

    def _start_of_month(self,
                        dt:  datetime,
                        ) -> datetime:
        """"""
        return datetime(dt.year, dt.month, 1)

    def _end_of_month(self,
                      dt:  datetime,
                      ) -> datetime:
        """"""
        from calendar import monthrange
        last_day = monthrange(dt.year, dt.month)[1]
        return datetime(dt.year, dt.month, last_day, 23, 59, 59, 999999)

    def _start_of_week(self,
                       dt:  datetime,
                       ) -> datetime:
        """"""
        start = dt - timedelta(days = dt.weekday())
        return datetime(start.year, start.month, start.day)

    def _end_of_week(self,
                     dt:  datetime,
                     ) -> datetime:
        """"""
        start = self._start_of_week(dt)
        end = start + timedelta(days = 6)
        return datetime(end.year, end.month, end.day, 23, 59, 59, 999999)

    def do_save(self) -> list:
        """"""
        return _serialize_data(self.frame.data['clauses'])

    def do_restore(self,
                   value: list,
                   ) ->   None:
        """"""
        try:
            self.set_data(*_deserialize_data(value))
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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

        table_columns = table.collect_schema().names()

        # Filter unvalid clauses from selection
        if table_columns:
            if self.frame.data['clauses']:
                clauses = []
                for clause in self.frame.data['clauses']:
                    column = clause[1]
                    if column in table_columns:
                        clauses.append(clause)
                self.frame.data['clauses'] = clauses

        if self.frame.data['all-columns'] != table_columns:
            self.frame.data['refresh-clauses'] = True

        self.frame.data['all-columns'] = table_columns

        if self.frame.data['refresh-clauses']:
            if len(self.frame.contents) == 3:
                content = self.frame.contents[-1]
                self.frame.remove_content(content)
            if table_columns:
                self._add_selector()

        if not self.frame.data['clauses']:
            self.frame.data['clause-expanded'] = True

        if self.frame.data['clause-expanded']:
            if len(self.frame.contents) == 3:
                widget = self.frame.contents[-1].Widget
                widget.set_expanded(True)

        self.frame.data['refresh-clauses'] = False

    def _add_selector(self) -> None:
        """"""
        def get_data() -> list:
            """"""
            return self.frame.data['clauses']

        def set_data(value: list) -> None:
            """"""
            if self.frame.data['clauses'] == value:
                return
            def callback(value: list) -> None:
                """"""
                self.frame.data['clauses'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        table = self.frame.data['table']
        tschema = table.collect_schema()

        widget = NodeFilterBuilder(get_data = get_data,
                                   set_data = set_data,
                                   tschema  = tschema)
        expander = Gtk.Expander(label = _('Clauses'),
                                child = widget)
        self.frame.add_content(expander)

        def on_expanded(widget:     Gtk.Widget,
                        param_spec: GObject.ParamSpec,
                        ) ->        None:
            """"""
            self.frame.data['clause-expanded'] = expander.get_expanded()

        expander.connect('notify::expanded', on_expanded)



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

        self.frame.data['all-columns']          = []
        self.frame.data['groupings']            = []
        self.frame.data['all-aggregations']     = {'count':       _('Count'),
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
        self.frame.data['aggregations']         = []
        self.frame.data['refresh-selector']     = False
        self.frame.data['grouping-expanded']    = False
        self.frame.data['aggregation-expanded'] = False

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
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_selector()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

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
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            if self.frame.data['grouping-expanded']:
                widget = self.frame.contents[2].Widget
                widget.set_expanded(True)

            if self.frame.data['aggregation-expanded']:
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
            _take_snapshot(self, callback, value)

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
            self.frame.data['grouping-expanded'] = expander.get_expanded()

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
            _take_snapshot(self, callback, value)

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
            self.frame.data['aggregation-expanded'] = expander.get_expanded()

        expander.connect('notify::expanded', on_aggregations_expanded)



class NodeTransposeTable(NodeTemplate):

    ndname = _('Transpose Table')

    action = 'transpose-table'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeTransposeTable(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['with-header'] = False

        self._add_output()
        self._add_input()
        self._add_with_header()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['with-header'] = args[0]

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

        if isinstance(table, LazyFrame):
            table = table.collect()

        with_header = self.frame.data['with-header']
        table = table.transpose(include_header = with_header)

        self.frame.data['table'] = table.lazy()

    def do_save(self) -> bool:
        """"""
        return self.frame.data['with-header']

    def do_restore(self,
                   value: bool,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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

    def _add_with_header(self) -> None:
        """"""
        def get_data() -> bool:
            """"""
            return self.frame.data['with-header']

        def set_data(value: bool) -> None:
            """"""
            def callback(value: bool) -> None:
                """"""
                self.frame.data['with-header'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        check = NodeCheckButton(title    = _('Include Header'),
                                get_data = get_data,
                                set_data = set_data)
        socket_type = NodeSocketType.INPUT
        self.frame.add_content(widget      = check,
                               socket_type = socket_type,
                               data_type   = bool,
                               get_data    = get_data,
                               set_data    = set_data)



class NodeReverseRows(NodeTemplate):

    ndname = _('Reverse Rows')

    action = 'reverse-rows'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeReverseRows(x, y)

        self.frame.do_process = self.do_process

        self._add_output()
        self._add_input()

        return self.frame

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

        table = table.reverse()

        self.frame.data['table'] = table

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
        label = NodeLabel(_('Table'), can_link = True)
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



class NodeChangeDataType(NodeTemplate):

    ndname = _('Change Data Type')

    action = 'change-data-type'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeChangeDataType(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['all-columns']  = []
        self.frame.data['maps']         = []
        self.frame.data['refresh-maps'] = True
        self.frame.data['map-expanded'] = False

        self._add_output()
        self._add_input()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['maps'] = args[0]
        self.frame.data['refresh-maps'] = True
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

        from polars import Date
        from polars import Time
        from polars import Datetime
        from polars import Duration
        from polars import String
        from polars import Boolean
        from polars import Categorical
        from polars import Float32
        from polars import Float64
        from polars import Int8
        from polars import Int16
        from polars import Int32
        from polars import Int64
        from polars import UInt8
        from polars import UInt16
        from polars import UInt32
        from polars import UInt64

        options = {
            'date':        Date,
            'time':        Time,
            'datetime':    Datetime,
            'duration':    Duration,
            'text':        String,
            'boolean':     Boolean,
            'categorical': Categorical,
            'float32':     Float32,
            'float64':     Float64,
            'int8':        Int8,
            'int16':       Int16,
            'int32':       Int32,
            'int64':       Int64,
            'uint8':       UInt8,
            'uint16':      UInt16,
            'uint32':      UInt32,
            'uint64':      UInt64,
        }

        if self.frame.data['all-columns']:
            if maps := self.frame.data['maps']:
                table = table.cast({m[0]: options[m[1]] for m in maps if m[1] in options})

        self.frame.data['table'] = table

    def do_save(self) -> list:
        """"""
        return deepcopy(self.frame.data['maps'])

    def do_restore(self,
                   value: list,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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

        table_columns = table.collect_schema().names()

        # Filter unvalid maps from selection
        if table_columns:
            if self.frame.data['maps']:
                maps = []
                for map in self.frame.data['maps']:
                    before, after = map
                    if before in table_columns:
                        maps.append(map)
                self.frame.data['maps'] = maps

        if self.frame.data['all-columns'] != table_columns:
            self.frame.data['refresh-maps'] = True

        self.frame.data['all-columns'] = table_columns

        if self.frame.data['refresh-maps']:
            if len(self.frame.contents) == 3:
                content = self.frame.contents[-1]
                self.frame.remove_content(content)
            if table_columns:
                self._add_selector()

        if not self.frame.data['maps']:
            self.frame.data['map-expanded'] = True

        if self.frame.data['map-expanded']:
            if len(self.frame.contents) == 3:
                widget = self.frame.contents[-1].Widget
                widget.set_expanded(True)

        self.frame.data['refresh-maps'] = False

    def _add_selector(self) -> None:
        """"""
        def get_data() -> list:
            """"""
            return self.frame.data['maps']

        def set_data(value: list) -> None:
            """"""
            def callback(value: list) -> None:
                """"""
                self.frame.data['maps'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        contents = [
            (
                'dropdown',
                {c: c for c in self.frame.data['all-columns']},
            ),
            (
                'dropdown',
                {
                    'date':        _('Date'),
                    'time':        _('Time'),
                    'datetime':    _('Datetime'),
                    'duration':    _('Duration'),
                    'text':        _('Text'),
                    'boolean':     _('Boolean'),
                    'categorical': _('Categorical'),
                    'float32':     _('Float (32-Bit)'),
                    'float64':     _('Float (64-Bit)'),
                    'int8':        _('Integer (8-Bit)'),
                    'int16':       _('Integer (16-Bit)'),
                    'int32':       _('Integer (32-Bit)'),
                    'int64':       _('Integer (64-Bit)'),
                    'uint8':       _('Unsigned (8-Bit)'),
                    'uint16':      _('Unsigned (16-Bit)'),
                    'uint32':      _('Unsigned (32-Bit)'),
                    'uint64':      _('Unsigned (64-Bit)'),
                },
            ),
        ]
        widget = NodeListItem(title    = _('Mapping'),
                              get_data = get_data,
                              set_data = set_data,
                              contents = contents)
        expander = Gtk.Expander(label = _('Mappings'),
                                child = widget)
        self.frame.add_content(expander)

        def on_expanded(widget:     Gtk.Widget,
                        param_spec: GObject.ParamSpec,
                        ) ->        None:
            """"""
            self.frame.data['map-expanded'] = expander.get_expanded()

        expander.connect('notify::expanded', on_expanded)



class NodeRenameColumns(NodeTemplate):

    ndname = _('Rename Columns')

    action = 'rename-columns'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeRenameColumns(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['all-columns']  = []
        self.frame.data['maps']         = []
        self.frame.data['refresh-maps'] = True
        self.frame.data['map-expanded'] = False

        self._add_output()
        self._add_input()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['maps'] = args[0]
        self.frame.data['refresh-maps'] = True
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

        if self.frame.data['all-columns']:
            if maps := self.frame.data['maps']:
                table = table.rename({m[0]: m[1] for m in maps if m[1].strip()})

        self.frame.data['table'] = table

    def do_save(self) -> list:
        """"""
        return deepcopy(self.frame.data['maps'])

    def do_restore(self,
                   value: list,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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

        table_columns = table.collect_schema().names()

        # Filter unvalid maps from selection
        if table_columns:
            if self.frame.data['maps']:
                maps = []
                for map in self.frame.data['maps']:
                    before, after = map
                    if before in table_columns:
                        maps.append(map)
                self.frame.data['maps'] = maps

        if self.frame.data['all-columns'] != table_columns:
            self.frame.data['refresh-maps'] = True

        self.frame.data['all-columns'] = table_columns

        if self.frame.data['refresh-maps']:
            if len(self.frame.contents) == 3:
                content = self.frame.contents[-1]
                self.frame.remove_content(content)
            if table_columns:
                self._add_selector()

        if not self.frame.data['maps']:
            self.frame.data['map-expanded'] = True

        if self.frame.data['map-expanded']:
            if len(self.frame.contents) == 3:
                widget = self.frame.contents[-1].Widget
                widget.set_expanded(True)

        self.frame.data['refresh-maps'] = False

    def _add_selector(self) -> None:
        """"""
        def get_data() -> list:
            """"""
            return self.frame.data['maps']

        def set_data(value: list) -> None:
            """"""
            def callback(value: list) -> None:
                """"""
                self.frame.data['maps'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        contents = [
            (
                'dropdown',
                {c: c for c in self.frame.data['all-columns']},
            ),
            ('entry'),
        ]
        widget = NodeListItem(title    = _('Mapping'),
                              get_data = get_data,
                              set_data = set_data,
                              contents = contents)
        expander = Gtk.Expander(label = _('Mappings'),
                                child = widget)
        self.frame.add_content(expander)

        def on_expanded(widget:     Gtk.Widget,
                        param_spec: GObject.ParamSpec,
                        ) ->        None:
            """"""
            self.frame.data['map-expanded'] = expander.get_expanded()

        expander.connect('notify::expanded', on_expanded)



class NodeReplaceValues(NodeTemplate):

    ndname = _('Replace Values')

    action = 'replace-values'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeReplaceValues(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['search']          = ''
        self.frame.data['replace']         = ''
        self.frame.data['options']         = []
        self.frame.data['all-columns']     = []
        self.frame.data['columns']         = []
        self.frame.data['refresh-columns'] = False
        self.frame.data['option-expanded'] = False
        self.frame.data['column-expanded'] = False

        self._add_output()
        self._add_input()
        self._add_search()
        self._add_replace()
        self._add_options_group()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['search']  = args[0]
        self.frame.data['replace'] = args[1]
        self.frame.data['options'] = args[2]
        self.frame.data['columns'] = args[3]

        widget = self.frame.contents[2].Widget
        widget.set_data(args[0])

        widget = self.frame.contents[3].Widget
        widget.set_data(args[1])

        widget = self.frame.contents[4].Widget
        widget = widget.get_child()
        widget = widget.get_first_child()
        widget.set_data(0 in args[2])
        widget = widget.get_next_sibling()
        widget.set_data(1 in args[2])
        widget = widget.get_next_sibling()
        widget.set_data(2 in args[2])

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

        table_schema = table.collect_schema()
        table_columns = table_schema.names()

        self.frame.data['table'] = table

        if not table_columns:
            return

        columns = self.frame.data['columns']

        if not columns:
            columns = self.frame.data['all-columns']

        from polars import col
        from polars import String

        expressions = []

        for column in columns:
            expression = col(column)
            try:
                if table_schema[column] == String:
                    expression = self._replace_text(expression,
                                                    self.frame.data['search'],
                                                    self.frame.data['replace'],
                                                    self.frame.data['options'])
                else:
                    expression = self._replace_non_text(expression,
                                                        self.frame.data['search'],
                                                        self.frame.data['replace'],
                                                        table_schema[column])
            except:
                continue
            expression = expression.name.keep()
            expressions.append(expression)

        self.frame.data['table'] = table.with_columns(expressions)

    def _replace_text(self,
                      expr:    Expr,
                      search:  str,
                      replace: str,
                      options: list,
                      ) ->     Expr:
        """"""
        from polars import when

        search = str(search) or None
        replace = str(replace)

        if not search:
            then_expr = expr.fill_null(replace)
            return when(expr.is_null()).then(then_expr).otherwise(expr)

        match_cell = 0 in options
        match_case = 1 in options
        use_regexp = 2 in options

        when_expr = expr.str.contains_any([search], ascii_case_insensitive = not match_case)
        if match_cell:
            when_expr = expr.str.to_lowercase() == search.lower()
            if match_case:
                when_expr = expr.str == search
        if use_regexp:
            when_expr = expr.str.contains(f'(?i){search}')
            if match_case:
                when_expr = expr.str.contains(search)

        if not use_regexp:
            from re import escape
            search = escape(search)
        if not match_case:
            search = f'(?i){search}'

        then_expr = expr.str.replace_all(search, replace)

        return when(when_expr).then(then_expr).otherwise(expr)

    def _replace_non_text(self,
                          expr:    Expr,
                          search:  str,
                          replace: str,
                          dtype:   DataType,
                          ) ->     Expr:
        """"""
        from polars import Datetime
        from polars import Date
        from polars import Time

        if dtype == Datetime:
            from ..core.utils import todatetime
            search = todatetime(search)
            replace = todatetime(replace)

        if dtype == Date:
            from ..core.utils import todate
            search = todate(search)
            replace = todate(replace)

        if dtype == Time:
            from ..core.utils import totime
            search = totime(search)
            replace = totime(replace)

        if dtype not in {Datetime, Date, Time}:
            from polars import Series
            search = Series([search]).cast(dtype).item()
            replace = Series([replace]).cast(dtype).item()

        return expr.replace(search, replace)

    def do_save(self) -> dict:
        """"""
        return {
            'search':  self.frame.data['search'],
            'replace': self.frame.data['replace'],
            'options': deepcopy(self.frame.data['options']),
            'columns': deepcopy(self.frame.data['columns']),
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['search'],
                          value['replace'],
                          value['options'],
                          value['columns'])
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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

    def _add_search(self) -> None:
        """"""
        def get_data() -> str:
            """"""
            return self.frame.data['search']

        def set_data(value: str) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                self.frame.data['search'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        entry = NodeEntry(title    = _('Search'),
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

            label = NodeLabel(_('Search'), can_link = True)
            label.insert_after(content.Container, content.Socket)

            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.data['bk.search'] = content.get_data()

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            if 'bk.search' in self.frame.data:
                content.set_data(self.frame.data['bk.search'])

            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink

    def _add_replace(self) -> None:
        """"""
        def get_data() -> str:
            """"""
            return self.frame.data['replace']

        def set_data(value: str) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                self.frame.data['replace'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        entry = NodeEntry(title    = _('Replace'),
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

            label = NodeLabel(_('Replace'), can_link = True)
            label.insert_after(content.Container, content.Socket)

            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.data['bk.replace'] = content.get_data()

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            if 'bk.replace' in self.frame.data:
                content.set_data(self.frame.data['bk.replace'])

            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink

    def _add_options_group(self) -> None:
        """"""
        box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        box.add_css_class('linked')

        box.append(self._add_exact_match())
        box.append(self._add_case_sensitive())
        box.append(self._add_regular_expression())

        expander = Gtk.Expander(label = _('Search Options'),
                                child = box)
        self.frame.add_content(expander)

    def _add_exact_match(self) -> None:
        """"""
        def get_data() -> bool:
            """"""
            return 0 in self.frame.data['options']

        def set_data(value: bool) -> None:
            """"""
            def callback(value: bool) -> None:
                """"""
                if value and 0 not in self.frame.data['options']:
                    self.frame.data['options'].append(0)
                if not value and 0 in self.frame.data['options']:
                    self.frame.data['options'].remove(0)
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        check = NodeCheckButton(title    = _('Exact Match'),
                                get_data = get_data,
                                set_data = set_data)

        return check

    def _add_case_sensitive(self) -> None:
        """"""
        def get_data() -> bool:
            """"""
            return 1 in self.frame.data['options']

        def set_data(value: bool) -> None:
            """"""
            def callback(value: bool) -> None:
                """"""
                if value and 1 not in self.frame.data['options']:
                    self.frame.data['options'].append(1)
                if not value and 1 in self.frame.data['options']:
                    self.frame.data['options'].remove(1)
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        check = NodeCheckButton(title    = _('Case Sensitive'),
                                get_data = get_data,
                                set_data = set_data)

        return check

    def _add_regular_expression(self) -> None:
        """"""
        def get_data() -> bool:
            """"""
            return 2 in self.frame.data['options']

        def set_data(value: bool) -> None:
            """"""
            def callback(value: bool) -> None:
                """"""
                if value and 2 not in self.frame.data['options']:
                    self.frame.data['options'].append(2)
                if not value and 2 in self.frame.data['options']:
                    self.frame.data['options'].remove(2)
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        check = NodeCheckButton(title    = _('Regular Expression'),
                                get_data = get_data,
                                set_data = set_data)

        return check

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
            if len(self.frame.contents) == 6:
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
        expander = Gtk.Expander(label = _('Search On'),
                                child = group)
        self.frame.add_content(expander)

        def on_expanded(widget:     Gtk.Widget,
                        param_spec: GObject.ParamSpec,
                        ) ->        None:
            """"""
            self.frame.data['column-expanded'] = expander.get_expanded()

        expander.connect('notify::expanded', on_expanded)



class NodeFillBlankCells(NodeTemplate):

    ndname = _('Fill Blank Cells')

    action = 'fill-blank-cells'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeFillBlankCells(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['options']         = {'forward':  _('Forward'),
                                              'backward': _('Backward'),
                                              'min':      _('Minimum'),
                                              'max':      _('Maximum'),
                                              'mean':     _('Mean'),
                                              'zero':     _('Zero'),
                                              'one':      _('One')}
        self.frame.data['strategy']        = 'forward'
        self.frame.data['all-columns']     = []
        self.frame.data['columns']         = []
        self.frame.data['refresh-columns'] = False
        self.frame.data['column-expanded'] = False

        self._add_output()
        self._add_input()
        self._add_strategy()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['strategy'] = args[0]
        self.frame.data['columns']  = args[1]

        options = self.frame.data['options']
        option = list(options.keys())[0]
        if args[0] in options:
            option = options[args[0]]
        widget = self.frame.contents[2].Widget
        widget.set_data(option)

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

        table_columns = table.collect_schema().names()

        strategy = self.frame.data['strategy']
        columns = self.frame.data['columns']

        from polars import col

        if table_columns and columns:
            expr = col(columns).fill_null(strategy = strategy)
            table = table.with_columns(expr)
        else:
            table = table.fill_null(strategy = strategy)

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'strategy': self.frame.data['strategy'],
            'columns':  deepcopy(self.frame.data['columns'])
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['strategy'],
                          value['columns'])
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Strategy'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['options'])
        self.frame.add_content(widget   = combo,
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
            if len(self.frame.contents) == 4:
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
        self.frame.add_content(expander)

        def on_expanded(widget:     Gtk.Widget,
                        param_spec: GObject.ParamSpec,
                        ) ->        None:
            """"""
            self.frame.data['column-expanded'] = expander.get_expanded()

        expander.connect('notify::expanded', on_expanded)



class NodeSplitColumnByDelimiter(NodeTemplate):

    ndname = _('Split Column by Delimiter')

    action = 'split-column-by-delimiter'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeSplitColumnByDelimiter(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns']      = []
        self.frame.data['column']       = ''
        self.frame.data['delimiter']    = ','
        self.frame.data['delimiters']   = {',':  _('Comma'),
                                           '=':  _('Equal Sign'),
                                           ';':  _('Semicolon'),
                                           ' ':  _('Space'),
                                           '\t': _('Tab'),
                                           '$':  _('Custom')}
        self.frame.data['ct.delimiter'] = False
        self.frame.data['n-columns']    = 0
        self.frame.data['split-ats']    = {'every': _('Every Occurrence'),
                                           'first': _('First Occurrence')}
        self.frame.data['split-at']     = 'every'

        self._add_output()
        self._add_input()
        self._add_column()
        self._add_delimiter()
        self._add_options()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column']    = args[0]
        self.frame.data['delimiter'] = args[1]
        self.frame.data['n-columns'] = args[2]
        self.frame.data['split-at']  = args[3]

        options = self.frame.data['delimiters']
        is_custom = args[1] not in options
        use_custom = self.frame.data['ct.delimiter']
        box = self.frame.contents[3].Widget
        combo = box.get_first_child()
        entry = combo.get_next_sibling()
        if is_custom and not use_custom:
            option = list(options.values())[-1]
            combo.set_data(option)
            entry.set_data(args[1])
            entry.set_visible(True)
            self.frame.data['ct.delimiter'] = True
        else:
            combo.set_data(options[args[1]])
            entry.set_visible(False)

        box = self.frame.contents[4].Widget
        spin = box.get_first_child()
        spin.set_data(args[2])

        options = self.frame.data['split-ats']
        option = list(options.keys())[0]
        if args[3] in options:
            option = options[args[3]]
        combo = spin.get_next_sibling()
        combo.set_data(option)
        combo.set_sensitive(args[2] > 0)

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            from polars import String

            column    = self.frame.data['column']
            delimiter = self.frame.data['delimiter']
            n_columns = self.frame.data['n-columns']
            split_at  = self.frame.data['split-at']

            expr = col(column)

            dtype = table.collect_schema()[column]
            if not isinstance(dtype, String):
                expr = expr.cast(String)

            if n_columns == 0:
                expr = expr.str.count_matches(delimiter)
                n_columns = table.select((expr + 1).max()).collect().item()

            if split_at == 'first':
                expr = expr.str.splitn(delimiter, n_columns)
            else:
                expr = expr.str.split_exact(delimiter, n_columns - 1)

            names = [f'{column}_{i}' for i in range(n_columns)]
            expr = expr.struct.rename_fields(names)
            table = table.with_columns(expr).unnest(column)

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'column':    self.frame.data['column'],
            'delimiter': self.frame.data['delimiter'],
            'n-columns': self.frame.data['n-columns'],
            'split-at':  self.frame.data['split-at'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['column'],
                          value['delimiter'],
                          value['n-columns'],
                          value['split-at'])
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

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
        box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        box.add_css_class('linked')
        self.frame.add_content(box)

        def get_custom() -> str:
            """"""
            return self.frame.data['delimiter']

        def set_custom(value: str) -> None:
            """"""
            def callback(value: str) -> None:
                """"""
                self.frame.data['delimiter'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        entry = NodeEntry(title    = _('Custom'),
                          get_data = get_custom,
                          set_data = set_custom)
        entry.set_visible(False)

        def get_data() -> str:
            """"""
            if self.frame.data['ct.delimiter']:
                return '$'
            return self.frame.data['delimiter']

        def set_data(value: str) -> None:
            """"""
            def callback(value: str) -> None:
                """"""
                if value == '$':
                    value = entry.get_text()
                    self.frame.data['delimiter'] = value
                    self.frame.data['ct.delimiter'] = True
                    entry.set_visible(True)
                else:
                    self.frame.data['delimiter'] = value
                    self.frame.data['ct.delimiter'] = False
                    entry.set_visible(False)
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Delimiter'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['delimiters'])

        box.append(combo)
        box.append(entry)

    def _add_options(self) -> None:
        """"""
        box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        box.add_css_class('linked')
        self.frame.add_content(box)

        def get_split_at() -> str:
            """"""
            return self.frame.data['split-at']

        def set_split_at(value: str) -> None:
            """"""
            def callback(value: str) -> None:
                """"""
                self.frame.data['split-at'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('At Delimiter'),
                                get_data = get_split_at,
                                set_data = set_split_at,
                                options  = self.frame.data['split-ats'])

        def get_n_columns() -> int:
            """"""
            return self.frame.data['n-columns']

        def set_n_columns(value: int) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                combo.set_sensitive(value > 0)
                self.frame.data['n-columns'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        spin = NodeSpinButton(title    = _('No. Columns'),
                              get_data = get_n_columns,
                              set_data = set_n_columns,
                              lower    = 0,
                              digits   = 0)

        box.append(spin)
        box.append(combo)



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
        option = list(options.keys())[0]
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
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

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
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

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
            _take_snapshot(self, callback, value)

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
            _take_snapshot(self, callback, value)

        widget = NodeComboButton(title    = _('Strategy'),
                                 get_data = get_data,
                                 set_data = set_data,
                                 options  = self.frame.data['strategies'])
        self.frame.add_content(widget   = widget,
                               get_data = get_data,
                               set_data = set_data)



class NodeSplitColumnByPositions(NodeTemplate):

    ndname = _('Split Column by Positions')

    action = 'split-column-by-positions'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeSplitColumnByPositions(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns']   = []
        self.frame.data['column']    = ''
        self.frame.data['positions'] = '0, 1'

        self._add_output()
        self._add_input()
        self._add_column()
        self._add_positions()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column']    = args[0]
        self.frame.data['positions'] = args[1]

        from ast import literal_eval
        widget = self.frame.contents[3].Widget
        widget.set_data(args[1])
        try:
            literal_eval(f'[{args[1]}]')
            widget.remove_css_class('error')
        except:
            widget.add_css_class('error')

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from ast import literal_eval
            from polars import col
            from polars import String
            from polars import struct

            column = self.frame.data['column']
            positions = self.frame.data['positions']

            try:
                positions = literal_eval(f'[{positions}]')
            except:
                positions = []
            else:
                positions = [abs(p) for p in positions]
                positions.sort()
                if positions[0] > 0:
                    positions.insert(0, 0)

            if positions:
                expr = col(column)

                dtype = table.collect_schema()[column]
                if not isinstance(dtype, String):
                    expr = expr.cast(String)

                exprs = []
                while positions:
                    offset = positions.pop(0)
                    length = None
                    if positions:
                        length = positions[0] - offset
                    slice_expr = expr.str.slice(offset, length)
                    exprs.append(slice_expr.alias(f'{column}_{len(exprs)}'))
                expr = struct(exprs)

                names = [f'{column}_{i}' for i in range(len(exprs))]
                expr = expr.struct.rename_fields(names)
                table = table.with_columns(expr.alias(column)).unnest(column)

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'column':    self.frame.data['column'],
            'positions': self.frame.data['positions'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['column'],
                          value['positions'])
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)

    def _add_positions(self) -> None:
        """"""
        widget = None

        def get_data() -> str:
            """"""
            return self.frame.data['positions']

        def set_data(value: str) -> None:
            """"""
            def callback(value: str) -> None:
                """"""
                from ast import literal_eval
                try:
                    literal_eval(f'[{value}]')
                    widget.remove_css_class('error')
                except:
                    widget.add_css_class('error')
                self.frame.data['positions'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        widget = NodeEntry(title    = _('Positions'),
                           get_data = get_data,
                           set_data = set_data)
        self.frame.add_content(widget   = widget,
                               get_data = get_data,
                               set_data = set_data)



class NodeSplitColumnByLowercaseToUppercase(NodeTemplate):

    ndname = _('Split Column by Lowercase to Uppercase')

    action = 'split-column-by-lowercase-to-uppercase'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeSplitColumnByLowercaseToUppercase(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            from string import ascii_lowercase
            from string import ascii_uppercase

            column = self.frame.data['column']

            before = list(ascii_lowercase)
            after  = list(ascii_uppercase)
            split_expr = col(column).strx.split_by_character_transition(before, after)
            upper_expr = table.select(split_expr.list.len().max()).collect().item()

            # FIXME: this process is expensive but it requires less memory
            # than if we choose to materialize the split for the unnesting
            # The software should be clever enough to make a decision when
            # to materialize things and when to not.
            struct_expr = col(column).list.to_struct(fields      = lambda i: f'{column}_{i}',
                                                     upper_bound = upper_expr)
            table = table.with_columns(split_expr.alias(column)) \
                         .with_columns(struct_expr) \
                         .unnest(column)

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeSplitColumnByUppercaseToLowercase(NodeTemplate):

    ndname = _('Split Column by Uppercase to Lowercase')

    action = 'split-column-by-uppercase-to-lowercase'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeSplitColumnByUppercaseToLowercase(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            from string import ascii_lowercase
            from string import ascii_uppercase

            column = self.frame.data['column']

            before = list(ascii_uppercase)
            after  = list(ascii_lowercase)
            split_expr = col(column).strx.split_by_character_transition(before, after)
            upper_expr = table.select(split_expr.list.len().max()).collect().item()

            struct_expr = col(column).list.to_struct(fields      = lambda i: f'{column}_{i}',
                                                     upper_bound = upper_expr)
            table = table.with_columns(split_expr.alias(column)) \
                         .with_columns(struct_expr) \
                         .unnest(column)

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeSplitColumnByDigitToNonDigit(NodeTemplate):

    ndname = _('Split Column by Digit to Non-Digit')

    action = 'split-column-by-digit-to-nondigit'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeSplitColumnByDigitToNonDigit(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            from string import ascii_letters
            from string import digits

            column = self.frame.data['column']

            before = list(digits)
            after  = list(ascii_letters)
            split_expr = col(column).strx.split_by_character_transition(before, after)
            upper_expr = table.select(split_expr.list.len().max()).collect().item()

            struct_expr = col(column).list.to_struct(fields      = lambda i: f'{column}_{i}',
                                                     upper_bound = upper_expr)
            table = table.with_columns(split_expr.alias(column)) \
                         .with_columns(struct_expr) \
                         .unnest(column)

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeSplitColumnByNonDigitToDigit(NodeTemplate):

    ndname = _('Split Column by Non-Digit to Digit')

    action = 'split-column-by-nondigit-to-digit'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeSplitColumnByNonDigitToDigit(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            from string import ascii_letters
            from string import digits

            column = self.frame.data['column']

            before = list(ascii_letters)
            after  = list(digits)
            split_expr = col(column).strx.split_by_character_transition(before, after)
            upper_expr = table.select(split_expr.list.len().max()).collect().item()

            struct_expr = col(column).list.to_struct(fields      = lambda i: f'{column}_{i}',
                                                     upper_bound = upper_expr)
            table = table.with_columns(split_expr.alias(column)) \
                         .with_columns(struct_expr) \
                         .unnest(column)

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeChangeCaseToLowercase(NodeTemplate):

    ndname = _('Change Case to Lowercase')

    action = 'change-case-to-lowercase'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeChangeCaseToLowercase(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            table = table.with_columns(col(column).str.to_lowercase())

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeChangeCaseToUppercase(NodeTemplate):

    ndname = _('Change Case to Uppercase')

    action = 'change-case-to-uppercase'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeChangeCaseToUppercase(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            table = table.with_columns(col(column).str.to_uppercase())

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeChangeCaseToTitleCase(NodeTemplate):

    ndname = _('Change Case to Title Case')

    action = 'change-case-to-titlecase'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeChangeCaseToTitleCase(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            table = table.with_columns(col(column).str.to_titlecase())

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeTrimContents(NodeTemplate):

    ndname = _('Trim Contents')

    action = 'trim-contents'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeTrimContents(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns']      = []
        self.frame.data['column']       = ''
        self.frame.data['character']    = ' '
        self.frame.data['characters']   = {' \n': _('Spaces & Newlines'),
                                           ' ':   _('Spaces Only'),
                                           '\n':  _('Newlines Only'),
                                           '$':   _('Custom')}
        self.frame.data['ct.character'] = False

        self._add_output()
        self._add_input()
        self._add_column()
        self._add_character()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column']    = args[0]
        self.frame.data['character'] = args[1]

        options = self.frame.data['characters']
        is_custom = args[1] not in options
        use_custom = self.frame.data['ct.character']
        box = self.frame.contents[3].Widget
        combo = box.get_first_child()
        entry = combo.get_next_sibling()
        if is_custom and not use_custom:
            option = list(options.values())[-1]
            combo.set_data(option)
            entry.set_data(args[1])
            entry.set_visible(True)
            self.frame.data['ct.character'] = True
        else:
            combo.set_data(options[args[1]])
            entry.set_visible(False)

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            character = self.frame.data['character']
            table = table.with_columns(col(column).str.strip_chars(character))

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'column':    self.frame.data['column'],
            'character': self.frame.data['character'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['column'],
                          value['character'])
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)

    def _add_character(self) -> None:
        """"""
        box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        box.add_css_class('linked')
        self.frame.add_content(box)

        def get_custom() -> str:
            """"""
            return self.frame.data['character']

        def set_custom(value: str) -> None:
            """"""
            def callback(value: str) -> None:
                """"""
                self.frame.data['character'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        entry = NodeEntry(title    = _('Custom'),
                          get_data = get_custom,
                          set_data = set_custom)
        entry.set_visible(False)

        def get_data() -> str:
            """"""
            if self.frame.data['ct.character']:
                return '$'
            return self.frame.data['character']

        def set_data(value: str) -> None:
            """"""
            def callback(value: str) -> None:
                """"""
                if value == '$':
                    value = entry.get_text()
                    self.frame.data['character'] = value
                    self.frame.data['ct.character'] = True
                    entry.set_visible(True)
                else:
                    self.frame.data['character'] = value
                    self.frame.data['ct.character'] = False
                    entry.set_visible(False)
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Characters'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['characters'])

        box.append(combo)
        box.append(entry)



class NodeCleanContents(NodeTemplate):

    ndname = _('Clean Contents')

    action = 'clean-contents'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCleanContents(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns']  = []
        self.frame.data['column']   = ''
        self.frame.data['to-keeps'] = []

        self._add_output()
        self._add_input()
        self._add_column()
        self._add_to_keeps_group()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column']   = args[0]
        self.frame.data['to-keeps'] = args[1]

        widget = self.frame.contents[3].Widget
        widget = widget.get_child()
        widget = widget.get_first_child()
        widget.set_data(0 in args[1])
        widget = widget.get_next_sibling()
        widget.set_data(1 in args[1])

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            to_keeps = self.frame.data['to-keeps']
            keep_newline = 0 in to_keeps
            keep_tab = 1 in to_keeps
            pattern = self._get_regex_pattern(keep_newline, keep_tab)
            table = table.with_columns(col(column).str.replace_all(pattern, ''))

        self.frame.data['table'] = table

    def _get_regex_pattern(self,
                           keep_newline: bool = False,
                           keep_tab:     bool = False,
                           ) ->          str:
        """"""
        excluded = set()

        if keep_newline:
            excluded.add(0x0A) # \n
        if keep_tab:
            excluded.add(0x09) # \t

        ranges = []

        def add_range(start: int,
                      end:   int,
                      ) ->   None:
            """"""
            chars = [i for i in range(start, end + 1) if i not in excluded]
            if chars:
                ranges.append(''.join(f'\\x{i:02X}' for i in chars))

        add_range(0x00, 0x1F)
        add_range(0x7F, 0x9F)

        return f'[{''.join(ranges)}]'

    def do_save(self) -> dict:
        """"""
        return {
            'column':   self.frame.data['column'],
            'to-keeps': self.frame.data['to-keeps'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['column'],
                          value['to-keeps'])
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)

    def _add_to_keeps_group(self) -> None:
        """"""
        box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        box.add_css_class('linked')

        box.append(self._add_newlines())
        box.append(self._add_tabs())

        expander = Gtk.Expander(label = _('To Keep'),
                                child = box)
        self.frame.add_content(expander)

    def _add_newlines(self) -> None:
        """"""
        def get_data() -> bool:
            """"""
            return 0 in self.frame.data['to-keeps']

        def set_data(value: bool) -> None:
            """"""
            def callback(value: bool) -> None:
                """"""
                if value and 0 not in self.frame.data['to-keeps']:
                    self.frame.data['to-keeps'].append(0)
                if not value and 0 in self.frame.data['to-keeps']:
                    self.frame.data['to-keeps'].remove(0)
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        check = NodeCheckButton(title    = _('Newlines'),
                                get_data = get_data,
                                set_data = set_data)

        return check

    def _add_tabs(self) -> None:
        """"""
        def get_data() -> bool:
            """"""
            return 1 in self.frame.data['to-keeps']

        def set_data(value: bool) -> None:
            """"""
            def callback(value: bool) -> None:
                """"""
                if value and 1 not in self.frame.data['to-keeps']:
                    self.frame.data['to-keeps'].append(1)
                if not value and 1 in self.frame.data['to-keeps']:
                    self.frame.data['to-keeps'].remove(1)
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        check = NodeCheckButton(title    = _('Tabs'),
                                get_data = get_data,
                                set_data = set_data)

        return check



class NodeAddPrefix(NodeTemplate):

    ndname = _('Add Prefix')

    action = 'add-prefix'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeAddPrefix(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''
        self.frame.data['prefix']  = ''

        self._add_output()
        self._add_input()
        self._add_column()
        self._add_prefix()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.data['prefix'] = args[1]

        widget = self.frame.contents[3].Widget
        widget.set_data(args[1])

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            from polars import String

            column = self.frame.data['column']
            prefix = self.frame.data['prefix']

            expr = col(column)

            dtype = table.collect_schema()[column]
            if not isinstance(dtype, String):
                expr = expr.cast(String)

            table = table.with_columns((prefix + expr).alias(column))

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'column': self.frame.data['column'],
            'prefix': self.frame.data['prefix'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['column'],
                          value['prefix'])
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)

    def _add_prefix(self) -> None:
        """"""
        def get_data() -> str:
            """"""
            return self.frame.data['prefix']

        def set_data(value: str) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                self.frame.data['prefix'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        entry = NodeEntry(title    = _('Prefix'),
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

            label = NodeLabel(_('Prefix'), can_link = True)
            label.insert_after(content.Container, content.Socket)

            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.data['bk.prefix'] = content.get_data()

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            if 'bk.prefix' in self.frame.data:
                content.set_data(self.frame.data['bk.prefix'])

            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink



class NodeAddSuffix(NodeTemplate):

    ndname = _('Add Suffix')

    action = 'add-suffix'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeAddSuffix(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''
        self.frame.data['suffix']  = ''

        self._add_output()
        self._add_input()
        self._add_column()
        self._add_suffix()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.data['suffix'] = args[1]

        widget = self.frame.contents[3].Widget
        widget.set_data(args[1])

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            from polars import String

            column = self.frame.data['column']
            suffix = self.frame.data['suffix']

            expr = col(column)

            dtype = table.collect_schema()[column]
            if not isinstance(dtype, String):
                expr = expr.cast(String)

            table = table.with_columns((expr + suffix).alias(column))

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'column': self.frame.data['column'],
            'suffix': self.frame.data['suffix'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['column'],
                          value['suffix'])
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)

    def _add_suffix(self) -> None:
        """"""
        def get_data() -> str:
            """"""
            return self.frame.data['suffix']

        def set_data(value: str) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                self.frame.data['suffix'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        entry = NodeEntry(title    = _('Suffix'),
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

            label = NodeLabel(_('Suffix'), can_link = True)
            label.insert_after(content.Container, content.Socket)

            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.data['bk.suffix'] = content.get_data()

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            if 'bk.suffix' in self.frame.data:
                content.set_data(self.frame.data['bk.suffix'])

            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink



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
        self.frame.data['ct.separator']    = False
        self.frame.data['alias'       ]    = ''
        self.frame.data['refresh-columns'] = False
        self.frame.data['column-expanded'] = False

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
        use_custom = self.frame.data['ct.separator']
        box = self.frame.contents[2].Widget
        combo = box.get_first_child()
        entry = combo.get_next_sibling()
        if is_custom and not use_custom:
            option = list(options.values())[-1]
            combo.set_data(option)
            entry.set_data(args[1])
            entry.set_visible(True)
            self.frame.data['ct.separator'] = True
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
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_selector()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

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
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        entry = NodeEntry(title    = _('Custom'),
                          get_data = get_custom,
                          set_data = set_custom)
        entry.set_visible(False)

        def get_data() -> str:
            """"""
            if self.frame.data['ct.separator']:
                return '$'
            return self.frame.data['separator']

        def set_data(value: str) -> None:
            """"""
            def callback(value: str) -> None:
                """"""
                if value == '$':
                    value = entry.get_text()
                    self.frame.data['separator'] = value
                    self.frame.data['ct.separator'] = True
                    entry.set_visible(True)
                else:
                    self.frame.data['separator'] = value
                    self.frame.data['ct.separator'] = False
                    entry.set_visible(False)
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

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
            _take_snapshot(self, callback, value)

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

        if self.frame.data['column-expanded']:
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
            _take_snapshot(self, callback, value)

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
            self.frame.data['column-expanded'] = expander.get_expanded()

        expander.connect('notify::expanded', on_expanded)



class NodeExtractTextLength(NodeTemplate):

    ndname = _('Extract Text Length')

    action = 'extract-text-length'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeExtractTextLength(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            from polars import String

            column = self.frame.data['column']

            expr = col(column)

            dtype = table.collect_schema()[column]
            if not isinstance(dtype, String):
                expr = expr.cast(String)

            table = table.with_columns(expr.str.len_chars())

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeExtractFirstCharacters(NodeTemplate):

    ndname = _('Extract First Characters')

    action = 'extract-first-characters'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeExtractFirstCharacters(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''
        self.frame.data['n-chars'] = 1

        self._add_output()
        self._add_input()
        self._add_column()
        self._add_n_chars()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column']  = args[0]
        self.frame.data['n-chars'] = args[1]

        widget = self.frame.contents[3].Widget
        widget.set_data(args[1])

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            from polars import String

            column = self.frame.data['column']
            offset = self.frame.data['n-chars']

            expr = col(column)

            dtype = table.collect_schema()[column]
            if not isinstance(dtype, String):
                expr = expr.cast(String)

            table = table.with_columns(expr.str.slice(0, offset))

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'column':  self.frame.data['column'],
            'n-chars': self.frame.data['n-chars'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['column'],
                          value['n-chars'])
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

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
            _take_snapshot(self, callback, value)

        widget = NodeSpinButton(title    = _('No. Characters'),
                                get_data = get_data,
                                set_data = set_data,
                                lower    = 1,
                                digits   = 0)
        self.frame.add_content(widget   = widget,
                               get_data = get_data,
                               set_data = set_data)



class NodeExtractLastCharacters(NodeTemplate):

    ndname = _('Extract Last Characters')

    action = 'extract-last-characters'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeExtractLastCharacters(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''
        self.frame.data['n-chars'] = 1

        self._add_output()
        self._add_input()
        self._add_column()
        self._add_n_chars()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column']  = args[0]
        self.frame.data['n-chars'] = args[1]

        widget = self.frame.contents[3].Widget
        widget.set_data(args[1])

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            from polars import String

            column = self.frame.data['column']
            offset = self.frame.data['n-chars']

            expr = col(column)

            dtype = table.collect_schema()[column]
            if not isinstance(dtype, String):
                expr = expr.cast(String)

            table = table.with_columns(expr.str.slice(-offset))

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'column':  self.frame.data['column'],
            'n-chars': self.frame.data['n-chars'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['column'],
                          value['n-chars'])
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

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
            _take_snapshot(self, callback, value)

        widget = NodeSpinButton(title    = _('No. Characters'),
                                get_data = get_data,
                                set_data = set_data,
                                lower    = 1,
                                digits   = 0)
        self.frame.add_content(widget   = widget,
                               get_data = get_data,
                               set_data = set_data)



class NodeExtractTextInRange(NodeTemplate):

    ndname = _('Extract Text in Range')

    action = 'extract-text-in-range'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeExtractTextInRange(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns']    = []
        self.frame.data['column']     = ''
        self.frame.data['from-index'] = 0
        self.frame.data['n-chars']    = 1

        self._add_output()
        self._add_input()
        self._add_column()
        self._add_from_index()
        self._add_n_chars()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column']     = args[0]
        self.frame.data['from-index'] = args[1]
        self.frame.data['n-chars']    = args[2]

        widget = self.frame.contents[3].Widget
        widget.set_data(args[1])

        widget = self.frame.contents[4].Widget
        widget.set_data(args[2])

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            from polars import String

            column = self.frame.data['column']
            offset = self.frame.data['from-index']
            length = self.frame.data['n-chars']

            expr = col(column)

            dtype = table.collect_schema()[column]
            if not isinstance(dtype, String):
                expr = expr.cast(String)

            table = table.with_columns(expr.str.slice(offset, length))

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'column':     self.frame.data['column'],
            'from-index': self.frame.data['from-index'],
            'n-chars':    self.frame.data['n-chars'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['column'],
                          value['from-index'],
                          value['n-chars'])
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)

    def _add_from_index(self) -> None:
        """"""
        def get_data() -> int:
            """"""
            return self.frame.data['from-index']

        def set_data(value: int) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                self.frame.data['from-index'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        widget = NodeSpinButton(title    = _('No. Characters'),
                                get_data = get_data,
                                set_data = set_data,
                                lower    = 1,
                                digits   = 0)
        self.frame.add_content(widget   = widget,
                               get_data = get_data,
                               set_data = set_data)

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
            _take_snapshot(self, callback, value)

        widget = NodeSpinButton(title    = _('No. Characters'),
                                get_data = get_data,
                                set_data = set_data,
                                lower    = 1,
                                digits   = 0)
        self.frame.add_content(widget   = widget,
                               get_data = get_data,
                               set_data = set_data)



class NodeExtractTextBeforeDelimiter(NodeTemplate):

    ndname = _('Extract Text Before Delimiter')

    action = 'extract-text-before-delimiter'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeExtractTextBeforeDelimiter(x, y)

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
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

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

            expr = expr.str.splitn(delimiter, 2).struct.field('field_0').fill_null('')
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
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

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
            _take_snapshot(self, callback, value)

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

            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.data['bk.delimiter'] = content.get_data()

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            if 'bk.delimiter' in self.frame.data:
                content.set_data(self.frame.data['bk.delimiter'])

            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink



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
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

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

            expr = expr.str.splitn(delimiter, 2).struct.field('field_1').fill_null('')
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
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

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
            _take_snapshot(self, callback, value)

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

            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.data['bk.delimiter'] = content.get_data()

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            if 'bk.delimiter' in self.frame.data:
                content.set_data(self.frame.data['bk.delimiter'])

            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink



class NodeExtractTextBetweenDelimiters(NodeTemplate):

    ndname = _('Extract Text Between Delimiters')

    action = 'extract-text-between-delimiters'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeExtractTextBetweenDelimiters(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''
        self.frame.data['start']   = ''
        self.frame.data['end']     = ''

        self._add_output()
        self._add_input()
        self._add_column()
        self._add_start()
        self._add_end()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.data['start']  = args[1]
        self.frame.data['end']    = args[2]

        widget = self.frame.contents[3].Widget
        widget.set_data(args[1])

        widget = self.frame.contents[4].Widget
        widget.set_data(args[2])

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            from polars import String
            from re import escape

            column = self.frame.data['column']
            start  = self.frame.data['start']
            end    = self.frame.data['end']

            expr = col(column)

            dtype = table.collect_schema()[column]
            if not isinstance(dtype, String):
                expr = expr.cast(String)

            start = escape(start)
            end   = escape(end)

            pattern = fr'{start}(.*?){end}'
            expr = expr.str.extract(pattern, 1).fill_null('')

            table = table.with_columns(expr.alias(column))

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'column': self.frame.data['column'],
            'start':  self.frame.data['start'],
            'end':    self.frame.data['end'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['column'],
                          value['start'],
                          value['end'])
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)

    def _add_start(self) -> None:
        """"""
        def get_data() -> str:
            """"""
            return self.frame.data['start']

        def set_data(value: str) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                self.frame.data['start'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        entry = NodeEntry(title    = _('Start'),
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

            label = NodeLabel(_('Start'), can_link = True)
            label.insert_after(content.Container, content.Socket)

            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.data['bk.start'] = content.get_data()

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            if 'bk.start' in self.frame.data:
                content.set_data(self.frame.data['bk.start'])

            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink

    def _add_end(self) -> None:
        """"""
        def get_data() -> str:
            """"""
            return self.frame.data['end']

        def set_data(value: str) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                self.frame.data['end'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        entry = NodeEntry(title    = _('End'),
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

            label = NodeLabel(_('End'), can_link = True)
            label.insert_after(content.Container, content.Socket)

            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.data['bk.end'] = content.get_data()

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            if 'bk.end' in self.frame.data:
                content.set_data(self.frame.data['bk.end'])

            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink



class NodeCalculateMinimum(NodeTemplate):

    ndname = _('Calculate Minimum')

    action = 'calculate-minimum'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateMinimum(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            column = self.frame.data['column']
            table = table.select(column).min()

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeCalculateMaximum(NodeTemplate):

    ndname = _('Calculate Maximum')

    action = 'calculate-maximum'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateMaximum(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            column = self.frame.data['column']
            table = table.select(column).max()

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeCalculateSummation(NodeTemplate):

    ndname = _('Calculate Summation')

    action = 'calculate-summation'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateSummation(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            column = self.frame.data['column']
            table = table.select(column).sum()

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeCalculateMedian(NodeTemplate):

    ndname = _('Calculate Median')

    action = 'calculate-median'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateMedian(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            column = self.frame.data['column']
            table = table.select(column).median()

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeCalculateAverage(NodeTemplate):

    ndname = _('Calculate Average')

    action = 'calculate-average'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateAverage(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            column = self.frame.data['column']
            table = table.select(column).mean()

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeCalculateStandardDeviation(NodeTemplate):

    ndname = _('Calculate Standard Deviation')

    action = 'calculate-standard-deviation'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateStandardDeviation(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            column = self.frame.data['column']
            table = table.select(column).std()

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeCountValues(NodeTemplate):

    ndname = _('Count Values')

    action = 'count-values'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCountValues(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            column = self.frame.data['column']
            table = table.select(column).count()

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeCountValues(NodeTemplate):

    ndname = _('Count Values')

    action = 'count-values'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCountValues(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            column = self.frame.data['column']
            table = table.select(column).count()

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeCountDistinctValues(NodeTemplate):

    ndname = _('Count Distinct Values')

    action = 'count-distinct-values'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCountDistinctValues(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            table = table.select(col(column).n_unique())

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeCalculateAddition(NodeTemplate):

    ndname = _('Calculate Addition')

    action = 'calculate-addition'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateAddition(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''
        self.frame.data['value']   = 0.0

        self._add_output()
        self._add_input()
        self._add_column()
        self._add_value()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        try:
            value = float(args[1])
        except:
            value = self.frame.data['value']

        self.frame.data['column'] = args[0]
        self.frame.data['value']  = value

        widget = self.frame.contents[3].Widget
        widget.set_data(value)

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            value = self.frame.data['value']
            table = table.with_columns(col(column) + value)

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'column': self.frame.data['column'],
            'value':  self.frame.data['value'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['column'],
                          value['value'])
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)

    def _add_value(self) -> None:
        """"""
        def get_data() -> float:
            """"""
            return self.frame.data['value']

        def set_data(value: float) -> None:
            """"""
            def callback(value: float) -> None:
                """"""
                self.frame.data['value'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        widget = NodeEntry(title    = _('Value'),
                           get_data = get_data,
                           set_data = set_data)
        content = self.frame.add_content(widget   = widget,
                                         get_data = get_data,
                                         set_data = set_data)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            content.Widget.set_visible(False)

            label = NodeLabel(_('Value'), can_link = True)
            label.insert_after(content.Container, content.Socket)

            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.data['bk.value'] = content.get_data()

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            if 'bk.value' in self.frame.data:
                content.set_data(self.frame.data['bk.value'])

            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink



class NodeCalculateMultiplication(NodeTemplate):

    ndname = _('Calculate Multiplication')

    action = 'calculate-multiplication'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateMultiplication(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''
        self.frame.data['value']   = 0.0

        self._add_output()
        self._add_input()
        self._add_column()
        self._add_value()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        try:
            value = float(args[1])
        except:
            value = self.frame.data['value']

        self.frame.data['column'] = args[0]
        self.frame.data['value']  = value

        widget = self.frame.contents[3].Widget
        widget.set_data(value)

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            value = self.frame.data['value']
            table = table.with_columns(col(column) * value)

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'column': self.frame.data['column'],
            'value':  self.frame.data['value'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['column'],
                          value['value'])
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)

    def _add_value(self) -> None:
        """"""
        def get_data() -> float:
            """"""
            return self.frame.data['value']

        def set_data(value: float) -> None:
            """"""
            def callback(value: float) -> None:
                """"""
                self.frame.data['value'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        widget = NodeEntry(title    = _('Value'),
                           get_data = get_data,
                           set_data = set_data)
        content = self.frame.add_content(widget   = widget,
                                         get_data = get_data,
                                         set_data = set_data)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            content.Widget.set_visible(False)

            label = NodeLabel(_('Value'), can_link = True)
            label.insert_after(content.Container, content.Socket)

            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.data['bk.value'] = content.get_data()

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            if 'bk.value' in self.frame.data:
                content.set_data(self.frame.data['bk.value'])

            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink



class NodeCalculateSubtraction(NodeTemplate):

    ndname = _('Calculate Subtraction')

    action = 'calculate-subtraction'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateSubtraction(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''
        self.frame.data['value']   = 0.0

        self._add_output()
        self._add_input()
        self._add_column()
        self._add_value()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        try:
            value = float(args[1])
        except:
            value = self.frame.data['value']

        self.frame.data['column'] = args[0]
        self.frame.data['value']  = value

        widget = self.frame.contents[3].Widget
        widget.set_data(value)

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            value = self.frame.data['value']
            table = table.with_columns(col(column) - value)

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'column': self.frame.data['column'],
            'value':  self.frame.data['value'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['column'],
                          value['value'])
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)

    def _add_value(self) -> None:
        """"""
        def get_data() -> float:
            """"""
            return self.frame.data['value']

        def set_data(value: float) -> None:
            """"""
            def callback(value: float) -> None:
                """"""
                self.frame.data['value'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        widget = NodeEntry(title    = _('Value'),
                           get_data = get_data,
                           set_data = set_data)
        content = self.frame.add_content(widget   = widget,
                                         get_data = get_data,
                                         set_data = set_data)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            content.Widget.set_visible(False)

            label = NodeLabel(_('Value'), can_link = True)
            label.insert_after(content.Container, content.Socket)

            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.data['bk.value'] = content.get_data()

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            if 'bk.value' in self.frame.data:
                content.set_data(self.frame.data['bk.value'])

            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink



class NodeCalculateDivision(NodeTemplate):

    ndname = _('Calculate Division')

    action = 'calculate-division'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateDivision(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''
        self.frame.data['value']   = 0.0

        self._add_output()
        self._add_input()
        self._add_column()
        self._add_value()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        try:
            value = float(args[1])
        except:
            value = self.frame.data['value']

        self.frame.data['column'] = args[0]
        self.frame.data['value']  = value

        widget = self.frame.contents[3].Widget
        widget.set_data(value)

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            value = self.frame.data['value']
            table = table.with_columns(col(column) / value)

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'column': self.frame.data['column'],
            'value':  self.frame.data['value'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['column'],
                          value['value'])
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)

    def _add_value(self) -> None:
        """"""
        def get_data() -> float:
            """"""
            return self.frame.data['value']

        def set_data(value: float) -> None:
            """"""
            def callback(value: float) -> None:
                """"""
                self.frame.data['value'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        widget = NodeEntry(title    = _('Value'),
                           get_data = get_data,
                           set_data = set_data)
        content = self.frame.add_content(widget   = widget,
                                         get_data = get_data,
                                         set_data = set_data)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            content.Widget.set_visible(False)

            label = NodeLabel(_('Value'), can_link = True)
            label.insert_after(content.Container, content.Socket)

            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.data['bk.value'] = content.get_data()

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            if 'bk.value' in self.frame.data:
                content.set_data(self.frame.data['bk.value'])

            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink



class NodeCalculateIntegerDivision(NodeTemplate):

    ndname = _('Calculate Integer-Division')

    action = 'calculate-integer-division'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateIntegerDivision(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''
        self.frame.data['value']   = 0.0

        self._add_output()
        self._add_input()
        self._add_column()
        self._add_value()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        try:
            value = float(args[1])
        except:
            value = self.frame.data['value']

        self.frame.data['column'] = args[0]
        self.frame.data['value']  = value

        widget = self.frame.contents[3].Widget
        widget.set_data(value)

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            value = self.frame.data['value']
            table = table.with_columns(col(column) // value)

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'column': self.frame.data['column'],
            'value':  self.frame.data['value'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['column'],
                          value['value'])
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)

    def _add_value(self) -> None:
        """"""
        def get_data() -> float:
            """"""
            return self.frame.data['value']

        def set_data(value: float) -> None:
            """"""
            def callback(value: float) -> None:
                """"""
                self.frame.data['value'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        widget = NodeEntry(title    = _('Value'),
                           get_data = get_data,
                           set_data = set_data)
        content = self.frame.add_content(widget   = widget,
                                         get_data = get_data,
                                         set_data = set_data)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            content.Widget.set_visible(False)

            label = NodeLabel(_('Value'), can_link = True)
            label.insert_after(content.Container, content.Socket)

            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.data['bk.value'] = content.get_data()

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            if 'bk.value' in self.frame.data:
                content.set_data(self.frame.data['bk.value'])

            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink



class NodeCalculateModulo(NodeTemplate):

    ndname = _('Calculate Modulo')

    action = 'calculate-modulo'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateModulo(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''
        self.frame.data['value']   = 0.0

        self._add_output()
        self._add_input()
        self._add_column()
        self._add_value()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        try:
            value = float(args[1])
        except:
            value = self.frame.data['value']

        self.frame.data['column'] = args[0]
        self.frame.data['value']  = value

        widget = self.frame.contents[3].Widget
        widget.set_data(value)

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            value = self.frame.data['value']
            table = table.with_columns(col(column) % value)

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'column': self.frame.data['column'],
            'value':  self.frame.data['value'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['column'],
                          value['value'])
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)

    def _add_value(self) -> None:
        """"""
        def get_data() -> float:
            """"""
            return self.frame.data['value']

        def set_data(value: float) -> None:
            """"""
            def callback(value: float) -> None:
                """"""
                self.frame.data['value'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        widget = NodeEntry(title    = _('Value'),
                           get_data = get_data,
                           set_data = set_data)
        content = self.frame.add_content(widget   = widget,
                                         get_data = get_data,
                                         set_data = set_data)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            content.Widget.set_visible(False)

            label = NodeLabel(_('Value'), can_link = True)
            label.insert_after(content.Container, content.Socket)

            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.data['bk.value'] = content.get_data()

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            if 'bk.value' in self.frame.data:
                content.set_data(self.frame.data['bk.value'])

            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink



class NodeCalculatePercentage(NodeTemplate):

    ndname = _('Calculate Percentage')

    action = 'calculate-percentage'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculatePercentage(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''
        self.frame.data['value']   = 0.0

        self._add_output()
        self._add_input()
        self._add_column()
        self._add_value()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        try:
            value = float(args[1])
        except:
            value = self.frame.data['value']

        self.frame.data['column'] = args[0]
        self.frame.data['value']  = value

        widget = self.frame.contents[3].Widget
        widget.set_data(value)

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            value = self.frame.data['value']
            table = table.with_columns(col(column) * value / 100)

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'column': self.frame.data['column'],
            'value':  self.frame.data['value'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['column'],
                          value['value'])
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)

    def _add_value(self) -> None:
        """"""
        def get_data() -> float:
            """"""
            return self.frame.data['value']

        def set_data(value: float) -> None:
            """"""
            def callback(value: float) -> None:
                """"""
                self.frame.data['value'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        widget = NodeEntry(title    = _('Value'),
                           get_data = get_data,
                           set_data = set_data)
        content = self.frame.add_content(widget   = widget,
                                         get_data = get_data,
                                         set_data = set_data)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            content.Widget.set_visible(False)

            label = NodeLabel(_('Value'), can_link = True)
            label.insert_after(content.Container, content.Socket)

            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.data['bk.value'] = content.get_data()

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            if 'bk.value' in self.frame.data:
                content.set_data(self.frame.data['bk.value'])

            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink



class NodeCalculatePercentOf(NodeTemplate):

    ndname = _('Calculate Percent Of')

    action = 'calculate-percent-of'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculatePercentOf(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''
        self.frame.data['value']   = 0.0

        self._add_output()
        self._add_input()
        self._add_column()
        self._add_value()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        try:
            value = float(args[1])
        except:
            value = self.frame.data['value']

        self.frame.data['column'] = args[0]
        self.frame.data['value']  = value

        widget = self.frame.contents[3].Widget
        widget.set_data(value)

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            value = self.frame.data['value']
            table = table.with_columns(col(column) / (value / 100))

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'column': self.frame.data['column'],
            'value':  self.frame.data['value'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['column'],
                          value['value'])
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)

    def _add_value(self) -> None:
        """"""
        def get_data() -> float:
            """"""
            return self.frame.data['value']

        def set_data(value: float) -> None:
            """"""
            def callback(value: float) -> None:
                """"""
                self.frame.data['value'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        widget = NodeEntry(title    = _('Value'),
                           get_data = get_data,
                           set_data = set_data)
        content = self.frame.add_content(widget   = widget,
                                         get_data = get_data,
                                         set_data = set_data)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            content.Widget.set_visible(False)

            label = NodeLabel(_('Value'), can_link = True)
            label.insert_after(content.Container, content.Socket)

            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.data['bk.value'] = content.get_data()

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            if 'bk.value' in self.frame.data:
                content.set_data(self.frame.data['bk.value'])

            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink



class NodeCalculateAbsolute(NodeTemplate):

    ndname = _('Calculate Absolute')

    action = 'calculate-absolute'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateAbsolute(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            table = table.with_columns(col(column).abs())

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeCalculateSquareRoot(NodeTemplate):

    ndname = _('Calculate Square Root')

    action = 'calculate-square-root'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateSquareRoot(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            table = table.with_columns(col(column).sqrt())

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeCalculateSquare(NodeTemplate):

    ndname = _('Calculate Square')

    action = 'calculate-square'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateSquare(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            table = table.with_columns(col(column) ** 2)

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeCalculateCube(NodeTemplate):

    ndname = _('Calculate Cube')

    action = 'calculate-cube'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateCube(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            table = table.with_columns(col(column) ** 3)

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeCalculatePowerK(NodeTemplate):

    ndname = _('Calculate Power K')

    action = 'calculate-power-k'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculatePowerK(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''
        self.frame.data['value']   = 1.0

        self._add_output()
        self._add_input()
        self._add_column()
        self._add_value()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        try:
            value = float(args[1])
        except:
            value = self.frame.data['value']

        self.frame.data['column'] = args[0]
        self.frame.data['value']  = value

        widget = self.frame.contents[3].Widget
        widget.set_data(value)

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            value = self.frame.data['value']
            table = table.with_columns(col(column) ** value)

        self.frame.data['table'] = table

    def do_save(self) -> dict:
        """"""
        return {
            'column': self.frame.data['column'],
            'value':  self.frame.data['value'],
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['column'],
                          value['value'])
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)

    def _add_value(self) -> None:
        """"""
        def get_data() -> float:
            """"""
            return self.frame.data['value']

        def set_data(value: float) -> None:
            """"""
            def callback(value: float) -> None:
                """"""
                self.frame.data['value'] = value
                self.frame.do_execute(backward = False)
            _take_snapshot(self, callback, value)

        widget = NodeEntry(title    = _('Value'),
                           get_data = get_data,
                           set_data = set_data)
        content = self.frame.add_content(widget   = widget,
                                         get_data = get_data,
                                         set_data = set_data)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            content.Widget.set_visible(False)

            label = NodeLabel(_('Value'), can_link = True)
            label.insert_after(content.Container, content.Socket)

            if not _iscompatible(pair_socket, self_content):
                return

            self.frame.data['bk.value'] = content.get_data()

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            content.Widget.set_visible(True)

            label = content.Socket.get_next_sibling()
            label.unparent()

            if 'bk.value' in self.frame.data:
                content.set_data(self.frame.data['bk.value'])

            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink



class NodeCalculateExponent(NodeTemplate):

    ndname = _('Calculate Exponent')

    action = 'calculate-exponent'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateExponent(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            table = table.with_columns(col(column).exp())

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeCalculateBase10(NodeTemplate):

    ndname = _('Calculate Base-10')

    action = 'calculate-base-10'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateBase10(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            table = table.with_columns(col(column).log10())

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeCalculateNatural(NodeTemplate):

    ndname = _('Calculate Natural')

    action = 'calculate-natural'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateNatural(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            table = table.with_columns(col(column).log())

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeCalculateSine(NodeTemplate):

    ndname = _('Calculate Sine')

    action = 'calculate-sine'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateSine(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            table = table.with_columns(col(column).sin())

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeCalculateCosine(NodeTemplate):

    ndname = _('Calculate Cosine')

    action = 'calculate-cosine'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateCosine(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            table = table.with_columns(col(column).cos())

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeCalculateTangent(NodeTemplate):

    ndname = _('Calculate Tangent')

    action = 'calculate-tangent'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateTangent(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            table = table.with_columns(col(column).tan())

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeCalculateArcsine(NodeTemplate):

    ndname = _('Calculate Arcsine')

    action = 'calculate-arcsine'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateArcsine(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            table = table.with_columns(col(column).arcsin())

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeCalculateArccosine(NodeTemplate):

    ndname = _('Calculate Arccosine')

    action = 'calculate-arccosine'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateArccosine(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            table = table.with_columns(col(column).arccos())

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeCalculateArctangent(NodeTemplate):

    ndname = _('Calculate Arctangent')

    action = 'calculate-arctangent'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateArctangent(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            table = table.with_columns(col(column).arctan())

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



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
        option = list(options.keys())[0]
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
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

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
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

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
            _take_snapshot(self, callback, value)

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
            _take_snapshot(self, callback, value)

        widget = NodeComboButton(title    = _('Mode'),
                                 get_data = get_data,
                                 set_data = set_data,
                                 options  = self.frame.data['modes'])
        self.frame.add_content(widget   = widget,
                               get_data = get_data,
                               set_data = set_data)



class NodeCalculateIsEven(NodeTemplate):

    ndname = _('Calculate Is Even')

    action = 'calculate-is-even'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateIsEven(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            table = table.with_columns(col(column) % 2 == 0)

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeCalculateIsOdd(NodeTemplate):

    ndname = _('Calculate Is Odd')

    action = 'calculate-is-odd'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCalculateIsOdd(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            table = table.with_columns(col(column) % 2 == 1)

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



class NodeExtractValueSign(NodeTemplate):

    ndname = _('Extract Value Sign')

    action = 'extract-value-sign'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeExtractValueSign(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['columns'] = []
        self.frame.data['column']  = ''

        self._add_output()
        self._add_input()
        self._add_column()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['column'] = args[0]
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_column()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        self.frame.data['table'] = table
        self._refresh_column()

        if self.frame.data['columns']:
            from polars import col
            column = self.frame.data['column']
            table = table.with_columns(col(column).sign())

        self.frame.data['table'] = table

    def do_save(self) -> str:
        """"""
        return self.frame.data['column']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

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
        label = NodeLabel(_('Table'), can_link = True)
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
            _take_snapshot(self, callback, value)

        combo = NodeComboButton(title    = _('Column'),
                                get_data = get_data,
                                set_data = set_data,
                                options  = self.frame.data['columns'])
        self.frame.add_content(widget   = combo,
                               get_data = get_data,
                               set_data = set_data)

        combo.set_sensitive(False)



_registered_nodes = [
    NodeBoolean(),
    NodeDecimal(),
    NodeInteger(),
    NodeString(),

    NodeReadFile(),
    NodeSheet(),
    NodeViewer(),

    NodeCustomFormula(),

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

    NodeSortRows(),
    NodeFilterRows(),

    NodeGroupBy(),
    NodeTransposeTable(),
    NodeReverseRows(),

    NodeChangeDataType(),
    NodeRenameColumns(),
    NodeReplaceValues(),
    NodeFillBlankCells(),

    NodeSplitColumnByDelimiter(),
    NodeSplitColumnByNumberOfCharacters(),
    NodeSplitColumnByPositions(),

    NodeSplitColumnByLowercaseToUppercase(),
    NodeSplitColumnByUppercaseToLowercase(),
    NodeSplitColumnByDigitToNonDigit(),
    NodeSplitColumnByNonDigitToDigit(),

    NodeChangeCaseToLowercase(),
    NodeChangeCaseToUppercase(),
    NodeChangeCaseToTitleCase(),

    NodeTrimContents(),
    NodeCleanContents(),

    NodeAddPrefix(),
    NodeAddSuffix(),

    NodeMergeColumns(),

    NodeExtractTextLength(),
    NodeExtractFirstCharacters(),
    NodeExtractLastCharacters(),
    NodeExtractTextInRange(),
    NodeExtractTextBeforeDelimiter(),
    NodeExtractTextAfterDelimiter(),
    NodeExtractTextBetweenDelimiters(),

    NodeCalculateMinimum(),
    NodeCalculateMaximum(),
    NodeCalculateSummation(),
    NodeCalculateMedian(),
    NodeCalculateAverage(),
    NodeCalculateStandardDeviation(),
    NodeCountValues(),
    NodeCountDistinctValues(),

    NodeCalculateAddition(),
    NodeCalculateMultiplication(),
    NodeCalculateSubtraction(),
    NodeCalculateDivision(),
    NodeCalculateIntegerDivision(),
    NodeCalculateModulo(),
    NodeCalculatePercentage(),
    NodeCalculatePercentOf(),

    NodeCalculateAbsolute(),
    NodeCalculateSquareRoot(),
    NodeCalculateSquare(),
    NodeCalculateCube(),
    NodeCalculatePowerK(),
    NodeCalculateExponent(),
    NodeCalculateBase10(),
    NodeCalculateNatural(),

    NodeCalculateSine(),
    NodeCalculateCosine(),
    NodeCalculateTangent(),
    NodeCalculateArcsine(),
    NodeCalculateArccosine(),
    NodeCalculateArctangent(),

    NodeRoundValue(),

    NodeCalculateIsEven(),
    NodeCalculateIsOdd(),
    NodeExtractValueSign(),
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
