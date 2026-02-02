# editor.py
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
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gtk
from polars import DataFrame
from polars import Float32
from polars import Float64
from polars import Int8
from polars import Int16
from polars import Int32
from polars import Int64
from polars import String
from polars import UInt8
from polars import UInt16
from polars import UInt32
from polars import UInt64
from typing import Any
from typing import TypeAlias
import gc

from ..core.datatable import DataTable
from ..node.frame import NodeFrame

Row:        TypeAlias = int
Column:     TypeAlias = int
Coordinate: TypeAlias = tuple[Row, Column]
Tables:     TypeAlias = dict[Coordinate, DataFrame]
Sparse:     TypeAlias = dict[Coordinate, Any]

FLOAT_TYPES   = {Float32, Float64}
INTEGER_TYPES = {Int8, Int16, Int32, Int64, UInt8, UInt16, UInt32, UInt64}

@Gtk.Template(resource_path = '/com/macipra/witt/sheet/editor.ui')
class SheetEditor(Gtk.Box):

    __gtype_name__ = 'SheetEditor'

    Container           = Gtk.Template.Child()
    Canvas              = Gtk.Template.Child()
    HorizontalScrollbar = Gtk.Template.Child()
    VerticalScrollbar   = Gtk.Template.Child()

    ICON_NAME     = 'table-symbolic'
    ACTION_PREFIX = 'sheet'

    title = GObject.Property(type = str, default = _('Sheet'))

    def __init__(self,
                 title:   str       = _('Sheet'),
                 tables:  Tables    = [],
                 sparse:  Sparse    = {},
                 configs: dict      = {},
                 node:    NodeFrame = None,
                 ) ->     None:
        """"""
        super().__init__()

        self.title = title

        self.configs = {
            'adjust-columns': True,
            'prefer-synchro': False,
            'view-read-only': False,
        }
        self.configs.update(configs)

        self.display   = SheetDisplay()
        self.document  = SheetDocument(self.Canvas,
                                       self.display)
        self.selection = SheetSelection(self.document,
                                        self.display)
        self.view      = SheetView(self.Canvas,
                                   self.HorizontalScrollbar,
                                   self.VerticalScrollbar,
                                   self.document,
                                   self.display,
                                   self.selection)

        self.selection.view = self.view

        self.node = node

        self._setup_actions()
        self._setup_commands()

        self.set_data(tables, sparse)

    def setup(self) -> None:
        """"""
        pass

    def grab_focus(self) -> None:
        """"""
        self.Canvas.set_focusable(True)
        self.Canvas.grab_focus()

    def refresh_ui(self,
                   refresh: bool = True,
                   ) ->     None:
        """"""
        # TODO: this potentially introduces unnecessary re-rendering
        # unless we can unsure that it does nothing when the scrolls
        # unchanged.
        self.view.update_by_scroll()

        from ..window import Window
        window = self.get_root()

        is_main_window = isinstance(window, Window)
        is_cursor_move = self.selection.current_cell_name != \
                         self.selection.previous_cell_name

        if is_main_window:
            if is_cursor_move:
                GLib.idle_add(window.Toolbar.populate)
            GLib.idle_add(window.StatusBar.populate)

        self.queue_draw(refresh)

    def cleanup(self) -> None:
        """"""
        pass

    def queue_draw(self,
                   refresh: bool = False,
                   ) ->     None:
        """"""
        if refresh:
            self.Canvas.cleanup()
        self.Canvas.queue_draw()

    def queue_resize(self) -> None:
        """"""
        vadjustment = self.VerticalScrollbar.get_adjustment()
        hadjustment = self.HorizontalScrollbar.get_adjustment()
        vadjustment.set_page_size(self.Canvas.get_height())
        hadjustment.set_page_size(self.Canvas.get_width())
        # FIXME: the scroll view jumps after resize the canvas
        # to smaller, scroll to the right end, and resize back
        # to larger then try scroll with the scroll bar handle

    def get_command_list(self) -> list[dict]:
        """"""
        from ..core.parser_command_context import Transformer
        from ..core.parser_command_context import parser

        variables = {}

        active_cell = self.selection.current_active_cell
        lcolumn = self.display.get_lcolumn_from_column(active_cell.column)
        lrow = self.display.get_lrow_from_row(active_cell.row)

        table, column_name = self.document.get_table_column_by_position(lcolumn, lrow)
        table_focus = isinstance(table, DataTable) and not table.placeholder

        n_all_tables = len(self.document.tables) # TODO
        n_table_columns = table.width if table_focus else 0

        variables['table_focus']           = table_focus
        variables['n_all_tables']          = n_all_tables
        variables['n_table_columns']       = n_table_columns
        variables['column_float_focus']    = False
        variables['column_string_focus']   = False
        variables['column_integer_focus']  = False
        variables['column_numeric_focus']  = False
        variables['column_temporal_focus'] = False

        if table_focus:
            column_dtype          = table.schema[column_name]
            column_string_focus   = column_dtype == String
            column_float_focus    = column_dtype in FLOAT_TYPES
            column_integer_focus  = column_dtype in INTEGER_TYPES
            column_numeric_focus  = column_dtype.is_numeric()
            column_temporal_focus = column_dtype.is_temporal()

            variables['column_float_focus']    = column_float_focus
            variables['column_string_focus']   = column_string_focus
            variables['column_integer_focus']  = column_integer_focus
            variables['column_numeric_focus']  = column_numeric_focus
            variables['column_temporal_focus'] = column_temporal_focus

        def isrelevant(context: str) -> bool:
            """"""
            if context is None:
                return True
            try:
                tree = parser.parse(context)
                transformer = Transformer(variables)
                return transformer.transform(tree)
            except:
                return False

        command_list = []
        for command in self._command_list:
            if not isrelevant(command['context']):
                continue
            command_list.append(command)

        return command_list

    def _setup_actions(self) -> None:
        """"""
        group = Gio.SimpleActionGroup.new()
        self.insert_action_group(self.ACTION_PREFIX, group)

        controller = Gtk.ShortcutController()
        self.add_controller(controller)

        def create_action(name:       str,
                          callback:   callable,
                          shortcuts:  list[str]        = [],
                          param_type: GLib.VariantType = None,
                          ) ->        None:
            """"""
            action = Gio.SimpleAction.new(name, param_type)
            action.connect('activate', callback)
            group.add_action(action)

            if shortcuts:
                trigger = Gtk.ShortcutTrigger.parse_string('|'.join(shortcuts))
                string_action = f'action({self.ACTION_PREFIX}.{name})'
                action = Gtk.ShortcutAction.parse_string(string_action)
                shortcut = Gtk.Shortcut.new(trigger, action)
                controller.add_shortcut(shortcut)

        create_action('open-file',              lambda *_: self.activate_action('app.open-file'))

        create_action('choose-columns',         lambda *_: self._transform_table('choose-columns'))
        create_action('remove-columns',         lambda *_: self._transform_table('remove-columns'))

        create_action('keep-top-k-rows',        lambda *_: self._transform_table('keep-top-k-rows'))
        create_action('keep-bottom-k-rows',     lambda *_: self._transform_table('keep-bottom-k-rows'))
        create_action('keep-first-k-rows',      lambda *_: self._transform_table('keep-first-k-rows'))
        create_action('keep-last-k-rows',       lambda *_: self._transform_table('keep-last-k-rows'))
        create_action('keep-range-of-rows',     lambda *_: self._transform_table('keep-range-of-rows'))
        create_action('keep-every-nth-rows',    lambda *_: self._transform_table('keep-every-nth-rows'))
        create_action('keep-duplicate-rows',    lambda *_: self._transform_table('keep-duplicate-rows'))

        create_action('remove-first-k-rows',    lambda *_: self._transform_table('remove-first-k-rows'))
        create_action('remove-last-k-rows',     lambda *_: self._transform_table('remove-last-k-rows'))
        create_action('remove-range-of-rows',   lambda *_: self._transform_table('remove-range-of-rows'))
        create_action('remove-duplicate-rows',  lambda *_: self._transform_table('remove-duplicate-rows'))

        create_action('sort-rows',              lambda *_: self._transform_table('sort-rows'))

        create_action('new-sheet',              lambda *_: self._add_new_worksheet('new-sheet'))

        create_action('transpose-table',        lambda *_: self._transform_table('transpose-table'))
        create_action('reverse-rows',           lambda *_: self._transform_table('reverse-rows'))

        create_action('convert-data-type',      lambda *_: self._transform_table('convert-data-type'))
        create_action('rename-columns',         lambda *_: self._transform_table('rename-columns'))
        create_action('replace-values',         lambda *_: self._transform_table('replace-values'))
        create_action('fill-blanks',            lambda *_: self._transform_table('fill-blanks'))

        create_action('split-column-by-'
                      'delimiter',              lambda *_: self._transform_table('split-column-by-delimiter'))
        create_action('split-column-by-'
                      'no-characters',          lambda *_: self._transform_table('split-column-by-no-characters'))
        create_action('split-column-by-'
                      'positions',              lambda *_: self._transform_table('split-column-by-positions'))

    def _setup_commands(self) -> None:
        """"""
        self._command_list = []

        def create_command(action_name: str,
                           title:       str,
                           name:        str          = None,
                           action_args: GLib.Variant = None,
                           shortcuts:   list[str]    = [],
                           context:     str          = 'table_focus',
                           prefix:      str          = 'sheet',
                           ) ->         None:
            """"""
            self._command_list.append({
                'name':        name or action_name,
                'title':       title,
                'shortcuts':   shortcuts,
                'action-name': f'{prefix}.{action_name}',
                'action-args': action_args,
                'context':     context,
            })

        def get_title_from_layout(action_name: str) -> str:
            """"""
            from .transform_layout import get_layout
            title, _ = get_layout(action_name)
            return title

        create_command(action_name = 'open-file',
                       title       = _('Open File...'),
                       shortcuts   = ['<Primary>o'],
                       context     = None,
                       prefix      = 'app')

        create_command('choose-columns',        f"{_('Table')}: {get_title_from_layout('choose-columns')}...")
        create_command('remove-columns',        f"{_('Table')}: {get_title_from_layout('remove-columns')}...")

        create_command('keep-rows',             '$placeholder')
        create_command('keep-top-k-rows',       f"{_('Table')}: {get_title_from_layout('keep-top-k-rows')}...")
        create_command('keep-bottom-k-rows',    f"{_('Table')}: {get_title_from_layout('keep-bottom-k-rows')}...")
        create_command('keep-first-k-rows',     f"{_('Table')}: {get_title_from_layout('keep-first-k-rows')}...")
        create_command('keep-last-k-rows',      f"{_('Table')}: {get_title_from_layout('keep-last-k-rows')}...")
        create_command('keep-range-of-rows',    f"{_('Table')}: {get_title_from_layout('keep-range-of-rows')}...")
        create_command('keep-every-nth-rows',   f"{_('Table')}: {get_title_from_layout('keep-every-nth-rows')}...")
        create_command('keep-duplicate-rows',   f"{_('Table')}: {get_title_from_layout('keep-duplicate-rows')}...")

        create_command('remove-rows',           '$placeholder')
        create_command('remove-first-k-rows',   f"{_('Table')}: {get_title_from_layout('remove-first-k-rows')}...")
        create_command('remove-last-k-rows',    f"{_('Table')}: {get_title_from_layout('remove-last-k-rows')}...")
        create_command('remove-range-of-rows',  f"{_('Table')}: {get_title_from_layout('remove-range-of-rows')}...")
        create_command('remove-duplicate-rows', f"{_('Table')}: {get_title_from_layout('remove-duplicate-rows')}...")

        create_command('sort-rows',             f"{_('Table')}: {get_title_from_layout('sort-rows')}...")

        create_command('new-sheet',             f"{_('Create')}: {_('Sheet')}",
                                                context = None)

        create_command('transpose-table',       f"{_('Table')}: {get_title_from_layout('transpose-table')}...")
        create_command('reverse-rows',          f"{_('Table')}: {get_title_from_layout('reverse-rows')}")

        create_command('convert-data-type',     f"{_('Table')}: {get_title_from_layout('convert-data-type')}...")
        create_command('rename-columns',        f"{_('Table')}: {get_title_from_layout('rename-columns')}...")
        create_command('replace-values',        f"{_('Table')}: {get_title_from_layout('replace-values')}...")
        create_command('fill-blanks',           f"{_('Table')}: {get_title_from_layout('fill-blanks')}...")

        create_command('split-column',          '$placeholder',
                                                context = 'table_focus and column_string_focus')
        create_command('split-column-by-'
                       'delimiter',             f"{_('Column')}: {get_title_from_layout('split-column-by-delimiter')}...",
                                                context = 'table_focus and column_string_focus')
        create_command('split-column-by-'
                       'no-characters',         f"{_('Column')}: {get_title_from_layout('split-column-by-no-characters')}...",
                                                context = 'table_focus and column_string_focus')
        create_command('split-column-by-'
                       'positions',             f"{_('Column')}: {get_title_from_layout('split-column-by-positions')}...",
                                                context = 'table_focus and column_string_focus')

    def set_data(self,
                 tables: Tables = [],
                 sparse: Sparse = {},
                 ) ->    None:
        """"""
        # Remove existing document widgets
        widgets = self.document.widgets
        for widgets in widgets.values():
            for widget in widgets:
                widget.unparent()

        while self.document.tables:
            del self.document.tables[0]

        # Create a new sheet document
        self.document = SheetDocument(self.Canvas,
                                      self.display)

        # Replace document reference to new one
        self.selection.document = self.document
        self.view.document      = self.document

        # Reset sheet display properties: column widths,
        # row heights, hidden columns, hidden rows, etc.
        self.display.reset()

        gc.collect()

        def do_finish(table: DataTable) -> None:
            """"""
            if self.configs['adjust-columns']:
                self._readjust_column_widths_by_table(table)

            c_cell = self.selection.current_cursor_cell
            c_lcol = self.display.get_lcolumn_from_column(c_cell.column)
            c_lrow = self.display.get_lrow_from_row(c_cell.row)

            c_cell_name = self.display.get_cell_name_from_position(c_lcol, c_lrow)
            a_cell_name = self.selection.current_cell_name

            self.selection.update_from_name(f'{c_cell_name}:{a_cell_name}')

            self.selection.previous_cell_name = ''

            self.refresh_ui()

        # Setup tables
        for coordinate, table in tables:
            table_index = self.document.create_table(table,
                                                     with_header = True,
                                                     column      = coordinate[0],
                                                     row         = coordinate[1],
                                                     prefer_sync = self.configs['prefer-synchro'],
                                                     on_finish   = do_finish)

            if self.configs['adjust-columns']:
                table = self.document.tables[table_index]
                self._readjust_column_widths_by_table(table)

        # Setup sparse
        for coordinate, value in sparse.items():
            self.document.create_or_update_sparse(value,
                                                  column = coordinate[0],
                                                  row    = coordinate[1])

            if self.configs['adjust-columns']:
                self._readjust_column_widths_by_value(value)

        self.Canvas.cleanup() # invalidate render caches

        cell_name = self.selection.current_cell_name or 'A1'
        self.selection.update_from_name(cell_name)

        self.selection.previous_cell_name = ''

        self.refresh_ui()

        gc.collect()

    def do_map(self) -> None:
        """"""
        Gtk.Box.do_map(self)

        def do_setup() -> bool:
            """"""
            parent = self.get_parent()

            if not parent:
                return Gdk.EVENT_STOP

            viewport_width = parent.get_width()
            viewport_height = parent.get_height()

            vadjustment = self.VerticalScrollbar.get_adjustment()
            hadjustment = self.HorizontalScrollbar.get_adjustment()
            vadjustment.set_page_size(viewport_height)
            hadjustment.set_page_size(viewport_width)

            return Gdk.EVENT_PROPAGATE

        GLib.idle_add(do_setup)

    def select_table_column(self,
                            table_name:  str,
                            column_name: str,
                            ) ->         None:
        """"""
        table = self.document.get_table_by_name(table_name)

        lrow = table.bounding_box.row
        lcolumn = table.bounding_box.column + table.columns.index(column_name)

        row = self.display.get_row_from_lrow(lrow)
        column = self.display.get_column_from_lcolumn(lcolumn)
        row_span = table.bounding_box.row_span - 1

        self.selection.update_from_position(column,
                                            row,
                                            column,
                                            row + row_span,
                                            follow_cursor = False)

    def resize_sheet_locators(self) -> None:
        """"""
        from gi.repository import Pango

        row_index = self.display.get_starting_row()
        max_row_number = row_index

        # Compute the last visible row number
        y = self.display.top_locator_height
        while y < self.Canvas.get_height():
            max_row_number = self.display.get_lrow_from_row(row_index)
            y += self.display.DEFAULT_CELL_HEIGHT
            row_index += 1

        context = self.Canvas.get_pango_context()
        font_desc = f'Monospace Normal Bold {self.display.FONT_SIZE}px'
        font_desc = Pango.font_description_from_string(font_desc)

        layout = Pango.Layout.new(context)
        layout.set_text(str(max_row_number), -1)
        layout.set_font_description(font_desc)

        text_width = layout.get_size()[0] / Pango.SCALE
        cell_padding = self.display.DEFAULT_CELL_PADDING
        locator_width = int(text_width + cell_padding * 2 + 0.5)
        locator_width = max(45, locator_width)

        if locator_width != self.display.left_locator_width:
            self.display.left_locator_width = locator_width
            self.Canvas.cleanup()

    def reposition_sheet_widgets(self) -> None:
        """"""
        self.document.reposition_table_widgets()

    def _readjust_column_widths_by_table(self,
                                         table: DataTable,
                                         ) ->   None:
        """"""
        from gi.repository import Pango
        from polars import col
        from polars import concat
        from polars import when
        from polars import Series
        from polars import String
        from polars import UInt32

        monitor = Gdk.Display.get_default().get_monitors()[0]
        max_width = monitor.get_geometry().width // 12
        sample_data = table.head(50).vstack(table.tail(50))

        context = self.Canvas.get_pango_context()
        font_desc = context.get_font_description()
        font_family = font_desc.get_family() if font_desc else 'Sans'
        font_desc = f'{font_family} Normal Bold {self.display.FONT_SIZE}px #tnum=1'
        font_desc = Pango.font_description_from_string(font_desc)

        layout = Pango.Layout.new(context)
        layout.set_wrap(Pango.WrapMode.NONE)
        layout.set_font_description(font_desc)

        table_right = table.bounding_box.column + table.bounding_box.column_span - 1
        n_column_widths = len(self.display.column_widths)

        # Initialize with default column widths
        if n_column_widths == 0:
            default_column_widths = [self.display.DEFAULT_CELL_WIDTH] * table_right
            self.display.column_widths = Series(default_column_widths, dtype = UInt32)
            n_column_widths = len(self.display.column_widths)

        # Expand with default column widths
        if n_column_widths < table_right:
            n_missing = table_right - n_column_widths
            default_column_widths = [self.display.DEFAULT_CELL_WIDTH] * n_missing
            default_column_widths = Series(default_column_widths, dtype = UInt32)
            self.display.column_widths = concat([self.display.column_widths,
                                                 default_column_widths])

        safe_margin = 0
        if table.width and table.height:
            from .widget import SheetTableFilter
            safe_margin += SheetTableFilter.WIDTH - 4

        for col_index, col_name in enumerate(table.columns):
            # Add table position offset into account
            col_index += table.bounding_box.column - 1

            # Compute text width of table header
            layout.set_text(col_name, -1)
            text_width = layout.get_pixel_size()[0]
            column_width = text_width + 2 * self.display.DEFAULT_CELL_PADDING
            column_width = column_width + safe_margin
            column_width = min(max_width, int(column_width))
            column_width = max(self.display.DEFAULT_CELL_WIDTH, column_width)
            self.display.column_widths[col_index] = column_width

            if table.height == 0:
                continue

            # Find longest table content
            try:
                expr = col(col_name).cast(String).fill_null('(Blank)')
                _sample_data = sample_data.with_columns(expr)

                expr = col(col_name).str.len_chars().max()
                max_length = _sample_data.select(expr).item()

                expr = col(col_name).str.len_chars() == max_length
                expr = when(expr).then(col(col_name)) \
                                 .otherwise(None) \
                                 .alias('sample_text')
                sample_text = _sample_data.with_columns(expr) \
                                          .drop_nulls('sample_text') \
                                          .sample(1) \
                                          .item(0, 'sample_text')
                sample_text = str(sample_text)

            # Assumes that the column is non-arbitrary dtype,
            # which is most likely a series, list, or struct.
            except Exception:
                self.display.column_widths[col_index] = max_width
                continue

            # Compute text width of table content
            current_column_width = self.display.column_widths[col_index]
            layout.set_text(sample_text, -1)
            text_width = layout.get_pixel_size()[0]
            column_width = text_width + 2 * self.display.DEFAULT_CELL_PADDING
            column_width = min(max_width, int(column_width))
            column_width = max(current_column_width, column_width)
            self.display.column_widths[col_index] = column_width

        self.display.ccolumn_widths = Series(self.display.column_widths).cum_sum()

        self.document.reposition_table_widgets()

    def _readjust_column_widths_by_value(self,
                                         value: Any,
                                         ) ->   None:
        """"""
        pass # TODO

    def _transform_table(self,
                         func_name: str,
                         func_args: list[Any] = [],
                         ) ->       None:
        """"""
        active = self.selection.current_active_cell

        lcolumn = self.display.get_lcolumn_from_column(active.column)
        lrow = self.display.get_lrow_from_row(active.row)

        table, column_name = self.document.get_table_column_by_position(lcolumn, lrow)

        if not isinstance(table, DataTable):
            return False

        window = self.get_root()
        editor = window.node_editor

        def do_reposition(curr_node: NodeFrame,
                          prev_node: NodeFrame) -> None:
            """"""
            # TODO: improve the overall placement algorithm
            offset_x = (prev_node.get_width() or 175)
            old_position = (curr_node.x, curr_node.y)
            new_position = (curr_node.x - offset_x - 50, curr_node.y)
            editor.move_node(curr_node, (old_position, new_position))
            prev_node = curr_node
            for content in curr_node.contents:
                if not (socket := content.Socket):
                    continue
                if not socket.is_input():
                    continue
                for link in socket.links:
                    curr_socket = link.in_socket
                    curr_node = curr_socket.Frame
                    do_reposition(curr_node, prev_node)
                prev_node = curr_node

        def do_transform(func_args: list[Any] = [],
                         **kwargs:  dict,
                         ) ->       bool:
            """"""
            window.history.grouping = True

            # Find the related node content
            contents = self.node.contents[1:-1]
            for content in contents:
                box = content.Widget
                label = box.get_first_child()
                label = label.get_label()
                if label == table.tname:
                    break

            # Find the pair node socket
            self_content = content
            self_socket = self_content.Socket
            link = self_socket.links[0]
            pair_socket = link.in_socket
            pair_node = pair_socket.Frame

            # Create a new appropriate node
            x = self.node.x - 175 - 50
            y = pair_node.y
            transformer = editor.create_node(func_name, x, y)
            transformer.set_data(*func_args)
            editor.add_node(transformer)

            # Manipulate so that the transformer node seem to
            # be reconnected to the sheet node
            self_content.node_uid = id(transformer)

            # Connect the pair node, new node, and self node
            content = transformer.contents[0]
            editor.add_link(content.Socket, self_socket)
            content = transformer.contents[1]
            editor.add_link(pair_socket, content.Socket)

            # Re-position all nodes to the left recursively
            do_reposition(pair_node, transformer)

            editor.select_by_click(transformer)

            window.history.grouping = False

            self.grab_focus()

        from .transform_layout import get_layout
        win_title, win_layout = get_layout(func_name)

        if len(win_layout) == 0:
            return do_transform(func_args)

        if not isinstance(win_layout, list):
            win_layout = [win_layout]

        column_strings  = [col for col in table.columns if table[col].dtype == String]
        column_floats   = [col for col in table.columns if table[col].dtype in FLOAT_TYPES]
        column_integers = [col for col in table.columns if table[col].dtype in INTEGER_TYPES]

        def do_evaluate(ridx: int,
                        rows: list[Any],
                        ) ->  None:
            """"""
            row = rows[ridx]
            var = row[-1]

            if isinstance(var, list):
                for vidx in range(len(var)):
                    do_evaluate(vidx, rows[ridx][-1])

            if isinstance(var, str):
                if not var.startswith('$'):
                    return

                if '-columns' in var:
                    check_all = var.endswith(':check-all')
                    var = var.removesuffix(':check-all')

                    use_column = var.endswith(':use-column')
                    var = var.removesuffix(':use-column')

                    rows[ridx] = list(rows[ridx])

                    if var == '$all-columns':
                        rows[ridx][-1] = table.columns
                    if var == '$string-columns':
                        rows[ridx][-1] = column_strings
                    if var == '$float-columns':
                        rows[ridx][-1] = column_floats
                    if var == '$integer-columns':
                        rows[ridx][-1] = column_integers

                    if check_all:
                        defaults = deepcopy(rows[ridx][-1])
                        rows[ridx].append(defaults)

                    if use_column:
                        defaults = [column_name]
                        rows[ridx].append(defaults)

                    rows[ridx] = tuple(rows[ridx])

        # Evaluate placeholders
        for ridx in range(len(win_layout)):
            do_evaluate(ridx, win_layout)

        window = self.get_root()
        application = window.get_application()

        subtitle = f'{self.title} – {table.tname}'

        from .transform_window import SheetTransformWindow
        dialog = SheetTransformWindow(title         = win_title,
                                      subtitle      = subtitle,
                                      layout        = win_layout,
                                      callback      = do_transform,
                                      transient_for = window,
                                      application   = application)
        dialog.present()

    def _add_new_worksheet(self,
                           name: str,
                           ) ->  None:
        """"""
        from ..node.repository import NodeViewer

        window = self.get_root()
        editor = window.node_editor

        window.history.grouping = True

        # Find the current active viewer node
        viewer = None
        for node in editor.nodes:
            if isinstance(node.parent, NodeViewer) and node.is_active():
                viewer = node
                break

        # TODO: improve the node placement algorithm

        # Create a new sheet node
        target_position = (viewer.x - 175 - 50, viewer.y)
        sheet = editor.create_node(name, *target_position)
        if sheet:
            editor.add_node(sheet)
            editor.select_by_click(sheet)

        # Link the sheet to the viewer node
        in_socket = sheet.contents[0].Socket
        out_socket = viewer.contents[-1].Socket
        editor.add_link(in_socket, out_socket)

        window.history.grouping = False

from .canvas import SheetCanvas
from .display import SheetDisplay
from .document import SheetDocument
from .selection import SheetSelection
from .view import SheetView
