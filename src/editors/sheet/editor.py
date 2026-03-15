# editor.py
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
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gtk
from polars        import LazyFrame
from polars        import Series
from polars        import Float32
from polars        import Float64
from polars        import Int8
from polars        import Int16
from polars        import Int32
from polars        import Int64
from polars        import String
from polars        import UInt8
from polars        import UInt16
from polars        import UInt32
from polars        import UInt64
from polars        import Date
from polars        import Time
from polars        import Datetime
from polars        import Duration
from typing        import Any

import gc

from ...core.construct    import *
from ...core.models.table import DataTable
from ..node.frame         import NodeFrame

FLOAT_TYPES    = {Float32, Float64}
INTEGER_TYPES  = {Int8, Int16, Int32, Int64, UInt8, UInt16, UInt32, UInt64}
TEMPORAL_TYPES = {Date, Time, Datetime, Duration}

@Gtk.Template(resource_path = '/com/wittara/studio/editors/sheet/editor.ui')
class SheetEditor(Gtk.Box):

    __gtype_name__ = 'SheetEditor'

    Container           = Gtk.Template.Child()
    FormulaBar          = Gtk.Template.Child()
    Canvas              = Gtk.Template.Child()
    HorizontalScrollbar = Gtk.Template.Child()
    VerticalScrollbar   = Gtk.Template.Child()

    ICON_NAME     = 'table-symbolic'
    ACTION_PREFIX = 'sheet'

    title = GObject.Property(type = str, default = _('Sheet'))

    adjust_columns = GObject.Property(type = bool, default = True)
    prefer_synchro = GObject.Property(type = bool, default = False)
    view_read_only = GObject.Property(type = bool, default = False)

    def __init__(self,
                 tables:   Tables    = {},
                 sparse:   Sparse    = {},
                 node:     NodeFrame = None,
                 **kwargs: dict,
                 ) ->      None:
        """"""
        super().__init__(**kwargs)

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

        if self.view_read_only:
            self.FormulaBar.set_visible(False)

    def grab_focus(self) -> None:
        """"""
        self.Canvas.set_focusable(True)
        self.Canvas.grab_focus()

    def refresh_ui(self,
                   refresh: bool = True,
                   ) ->     None:
        """"""
        from ...ui.window.widget import Window
        window = self.get_root()

        is_main_window = isinstance(window, Window)
        is_cursor_move = self.selection.current_cell_name != \
                         self.selection.previous_cell_name

        if is_main_window:
            if is_cursor_move:
                GLib.idle_add(window.Toolbar.populate)
            GLib.idle_add(window.StatusBar.populate)

        self.view.update_by_scroll()
        self.update_formula_bar()
        self.queue_draw(refresh)

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
        from ...core.evaluators.context import Evaluator

        variables = {}

        table, column_name = self._get_active_table_context()
        table_focus = isinstance(table, DataTable) and not table.placeholder

        n_tables = len(self.document.tables)
        n_columns = table.width if table_focus else 0

        n_tables_all = len(self.get_all_tables())

        variables['table_focus']  = table_focus
        variables['n_tables']     = n_tables
        variables['n_columns']    = n_columns
        variables['n_tables_all'] = n_tables_all

        variables['string_focus']   = False
        variables['float_focus']    = False
        variables['integer_focus']  = False
        variables['numeric_focus']  = False
        variables['temporal_focus'] = False

        if table_focus:
            column_dtype   = table.schema[column_name]
            string_focus   = column_dtype == String
            float_focus    = column_dtype in FLOAT_TYPES
            integer_focus  = column_dtype in INTEGER_TYPES
            numeric_focus  = column_dtype.is_numeric()
            temporal_focus = column_dtype.is_temporal()

            variables['string_focus']   = string_focus
            variables['float_focus']    = float_focus
            variables['integer_focus']  = integer_focus
            variables['numeric_focus']  = numeric_focus
            variables['temporal_focus'] = temporal_focus

            target_dtypes = []
            if string_focus:
                target_dtypes += [String]
            if float_focus:
                target_dtypes += list(FLOAT_TYPES)
            if integer_focus:
                target_dtypes += list(INTEGER_TYPES)
            if numeric_focus:
                target_dtypes += list(FLOAT_TYPES)
                target_dtypes += list(INTEGER_TYPES)
            if temporal_focus:
                target_dtypes += list(TEMPORAL_TYPES)
            target_dtypes = set(target_dtypes)

            if target_dtypes:
                from polars import col
                variables['n_columns'] = table.select(col(target_dtypes)).width

        def isrelevant(context: str) -> bool:
            """"""
            if context is None:
                return True
            try:
                return Evaluator(variables).evaluate(context)
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
        create_action('open-database',          lambda *_: self.activate_action('app.open-database'))

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
        create_action('filter-rows',            lambda *_: self._filter_rows())

        create_action('new-sheet',              lambda *_: self._add_new_workspace('new-sheet'))
        create_action('custom-formula',         lambda *_: self._write_custom_formula())

        create_action('join-tables',            lambda *_: self._join_tables())
        create_action('group-by',               lambda *_: self._transform_table('group-by'))
        create_action('transpose-table',        lambda *_: self._transform_table('transpose-table'))
        create_action('reverse-rows',           lambda *_: self._transform_table('reverse-rows'))

        create_action('change-data-type',       lambda *_: self._transform_table('change-data-type'))
        create_action('rename-columns',         lambda *_: self._transform_table('rename-columns'))
        create_action('replace-values',         lambda *_: self._transform_table('replace-values'))
        create_action('fill-blank-values',      lambda *_: self._transform_table('fill-blank-values'))

        create_action('split-column-by-'
                      'delimiter',              lambda *_: self._transform_table('split-column-by-delimiter'))
        create_action('split-column-by-'
                      'number-of-characters',   lambda *_: self._transform_table('split-column-by-number-of-characters'))
        create_action('split-column-by-'
                      'positions',              lambda *_: self._transform_table('split-column-by-positions'))
        create_action('split-column-by-'
                      'lowercase-to-uppercase', lambda *_: self._transform_table('split-column-by-lowercase-to-uppercase'))
        create_action('split-column-by-'
                      'uppercase-to-lowercase', lambda *_: self._transform_table('split-column-by-uppercase-to-lowercase'))
        create_action('split-column-by-'
                      'digit-to-nondigit',      lambda *_: self._transform_table('split-column-by-digit-to-nondigit'))
        create_action('split-column-by-'
                      'nondigit-to-digit',      lambda *_: self._transform_table('split-column-by-nondigit-to-digit'))

        create_action('change-case-to-'
                      'lowercase',              lambda *_: self._transform_table('change-case-to-lowercase'))
        create_action('change-case-to-'
                      'uppercase',              lambda *_: self._transform_table('change-case-to-uppercase'))
        create_action('change-case-to-'
                      'titlecase',              lambda *_: self._transform_table('change-case-to-titlecase'))

        create_action('trim-contents',          lambda *_: self._transform_table('trim-contents'))
        create_action('clean-contents',         lambda *_: self._transform_table('clean-contents'))

        create_action('add-prefix',             lambda *_: self._transform_table('add-prefix'))
        create_action('add-suffix',             lambda *_: self._transform_table('add-suffix'))

        create_action('merge-columns',          lambda *_: self._transform_table('merge-columns'))

        create_action('extract-text-length',    lambda *_: self._transform_table('extract-text-length'))
        create_action('extract-first-'
                      'characters',             lambda *_: self._transform_table('extract-first-characters'))
        create_action('extract-last-'
                      'characters',             lambda *_: self._transform_table('extract-last-characters'))
        create_action('extract-text-in-range',  lambda *_: self._transform_table('extract-text-in-range'))
        create_action('extract-text-before-'
                      'delimiter',              lambda *_: self._transform_table('extract-text-before-delimiter'))
        create_action('extract-text-after-'
                      'delimiter',              lambda *_: self._transform_table('extract-text-after-delimiter'))
        create_action('extract-text-between-'
                      'delimiters',             lambda *_: self._transform_table('extract-text-between-delimiters'))

        create_action('calculate-summation',    lambda *_: self._transform_table('calculate-summation'))
        create_action('calculate-minimum',      lambda *_: self._transform_table('calculate-minimum'))
        create_action('calculate-maximum',      lambda *_: self._transform_table('calculate-maximum'))
        create_action('calculate-median',       lambda *_: self._transform_table('calculate-median'))
        create_action('calculate-average',      lambda *_: self._transform_table('calculate-average'))
        create_action('calculate-standard-'
                      'deviation',              lambda *_: self._transform_table('calculate-standard-deviation'))
        create_action('count-values',           lambda *_: self._transform_table('count-values'))
        create_action('count-distinct-values',  lambda *_: self._transform_table('count-distinct-values'))

        create_action('calculate-addition',     lambda *_: self._transform_table('calculate-addition'))
        create_action('calculate-'
                      'multiplication',         lambda *_: self._transform_table('calculate-multiplication'))
        create_action('calculate-subtraction',  lambda *_: self._transform_table('calculate-subtraction'))
        create_action('calculate-division',     lambda *_: self._transform_table('calculate-division'))
        create_action('calculate-integer-'
                      'division',               lambda *_: self._transform_table('calculate-integer-division'))
        create_action('calculate-modulo',       lambda *_: self._transform_table('calculate-modulo'))
        create_action('calculate-percentage',   lambda *_: self._transform_table('calculate-percentage'))
        create_action('calculate-percent-of',   lambda *_: self._transform_table('calculate-percent-of'))

        create_action('calculate-absolute',     lambda *_: self._transform_table('calculate-absolute'))
        create_action('calculate-square-root',  lambda *_: self._transform_table('calculate-square-root'))
        create_action('calculate-square',       lambda *_: self._transform_table('calculate-square'))
        create_action('calculate-cube',         lambda *_: self._transform_table('calculate-cube'))
        create_action('calculate-power-k',      lambda *_: self._transform_table('calculate-power-k'))
        create_action('calculate-exponent',     lambda *_: self._transform_table('calculate-exponent'))
        create_action('calculate-base-10',      lambda *_: self._transform_table('calculate-base-10'))
        create_action('calculate-natural',      lambda *_: self._transform_table('calculate-natural'))

        create_action('calculate-sine',         lambda *_: self._transform_table('calculate-sine'))
        create_action('calculate-cosine',       lambda *_: self._transform_table('calculate-cosine'))
        create_action('calculate-tangent',      lambda *_: self._transform_table('calculate-tangent'))
        create_action('calculate-arcsine',      lambda *_: self._transform_table('calculate-arcsine'))
        create_action('calculate-arccosine',    lambda *_: self._transform_table('calculate-arccosine'))
        create_action('calculate-arctangent',   lambda *_: self._transform_table('calculate-arctangent'))

        create_action('round-value',            lambda *_: self._transform_table('round-value'))

        create_action('calculate-is-even',      lambda *_: self._transform_table('calculate-is-even'))
        create_action('calculate-is-odd',       lambda *_: self._transform_table('calculate-is-odd'))
        create_action('extract-value-sign',     lambda *_: self._transform_table('extract-value-sign'))

        create_action('quick-sort-rows',        callback   = self._quick_sort_rows,
                                                param_type = GLib.VariantType('s'))
        create_action('clear-sort-rows',        callback   = self._clear_sort_rows)

        create_action('clear-filter-rows',      callback   = self._clear_filter_rows)

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
            from .ui.transform_layout import get_layout
            title, _ = get_layout(action_name)
            return title

        create_command('open-source',           '$placeholder',
                                                context = None)

        create_command('open-file',             title     = _('Open File...'),
                                                shortcuts = ['<Primary>o'],
                                                context   = None,
                                                prefix    = 'app')
        create_command('open-database',         title     = _('Open Database...'),
                                                shortcuts = ['<Shift><Primary>o'],
                                                context   = None,
                                                prefix    = 'app')

        create_command('focus-name-box',        title     = _('Focus Name Box'),
                                                shortcuts = ['<Primary>g'],
                                                context   = None,
                                                prefix    = 'formula')
        create_command('focus-formula-box',     title     = _('Focus Formula Box'),
                                                shortcuts = ['F2'],
                                                context   = None,
                                                prefix    = 'formula')

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
        create_command('filter-rows',           f"{_('Table')}: {_('Filter Rows')}...")

        create_command('new-workspace',         '$placeholder',
                                                context = None)
        create_command('new-sheet',             f"{_('Create')}: {_('Sheet')}",
                                                context = None)
        create_command('custom-formula',        f"{_('Table')}: {_('Write Custom Formula')}...")

        create_command('join-tables',           f"{_('Table')}: {_('Join Tables')}...",
                                                context = 'table_focus and n_tables_all > 1')
        create_command('group-by',              f"{_('Table')}: {get_title_from_layout('group-by')}...")
        create_command('transpose-table',       f"{_('Table')}: {get_title_from_layout('transpose-table')}...")
        create_command('reverse-rows',          f"{_('Table')}: {get_title_from_layout('reverse-rows')}")

        create_command('change-data-type',      f"{_('Table')}: {get_title_from_layout('change-data-type')}...")
        create_command('rename-columns',        f"{_('Table')}: {get_title_from_layout('rename-columns')}...")
        create_command('replace-values',        f"{_('Table')}: {get_title_from_layout('replace-values')}...")
        create_command('fill-blank-values',     f"{_('Table')}: {get_title_from_layout('fill-blank-values')}...")

        create_command('split-column',          '$placeholder')
        create_command('split-column-by-'
                       'delimiter',             f"{_('Column')}: {get_title_from_layout('split-column-by-delimiter')}...")
        create_command('split-column-by-'
                       'number-of-characters',  f"{_('Column')}: {get_title_from_layout('split-column-by-number-of-characters')}...")
        create_command('split-column-by-'
                       'positions',             f"{_('Column')}: {get_title_from_layout('split-column-by-positions')}...")
        create_command('split-column-by-'
                       'lowercase-to-'
                       'uppercase',             f"{_('Column')}: {get_title_from_layout('split-column-by-lowercase-to-uppercase')}...",
                                                context = 'table_focus and string_focus')
        create_command('split-column-by-'
                       'uppercase-to-'
                       'lowercase',             f"{_('Column')}: {get_title_from_layout('split-column-by-uppercase-to-lowercase')}...",
                                                context = 'table_focus and string_focus')
        create_command('split-column-by-'
                       'digit-to-nondigit',     f"{_('Column')}: {get_title_from_layout('split-column-by-digit-to-nondigit')}...",
                                                context = 'table_focus and string_focus')
        create_command('split-column-by-'
                       'nondigit-to-digit',     f"{_('Column')}: {get_title_from_layout('split-column-by-nondigit-to-digit')}...",
                                                context = 'table_focus and string_focus')

        create_command('format-column',         '$placeholder')
        create_command('change-case-to-'
                       'lowercase',             f"{_('Column')}: {get_title_from_layout('change-case-to-lowercase')}...",
                                                context = 'table_focus and string_focus')
        create_command('change-case-to-'
                       'uppercase',             f"{_('Column')}: {get_title_from_layout('change-case-to-uppercase')}...",
                                                context = 'table_focus and string_focus')
        create_command('change-case-to-'
                       'titlecase',             f"{_('Column')}: {get_title_from_layout('change-case-to-titlecase')}...",
                                                context = 'table_focus and string_focus')
        create_command('trim-contents',         f"{_('Column')}: {get_title_from_layout('trim-contents')}...",
                                                context = 'table_focus and string_focus')
        create_command('clean-contents',        f"{_('Column')}: {get_title_from_layout('clean-contents')}...",
                                                context = 'table_focus and string_focus')
        create_command('add-prefix',            f"{_('Column')}: {get_title_from_layout('add-prefix')}...")
        create_command('add-suffix',            f"{_('Column')}: {get_title_from_layout('add-suffix')}...")

        create_command('merge-columns',         f"{_('Column')}: {get_title_from_layout('merge-columns')}...")

        create_command('extract-column',        '$placeholder')
        create_command('extract-text-length',   f"{_('Column')}: {get_title_from_layout('extract-text-length')}...")
        create_command('extract-first-'
                       'characters',            f"{_('Column')}: {get_title_from_layout('extract-first-characters')}...")
        create_command('extract-last-'
                       'characters',            f"{_('Column')}: {get_title_from_layout('extract-last-characters')}...")
        create_command('extract-text-in-range', f"{_('Column')}: {get_title_from_layout('extract-text-in-range')}...")
        create_command('extract-text-before-'
                       'delimiter',             f"{_('Column')}: {get_title_from_layout('extract-text-before-delimiter')}...")
        create_command('extract-text-after-'
                       'delimiter',             f"{_('Column')}: {get_title_from_layout('extract-text-after-delimiter')}...")
        create_command('extract-text-between-'
                       'delimiters',            f"{_('Column')}: {get_title_from_layout('extract-text-between-delimiters')}...")

        create_command('column-statistics',     '$placeholder')
        create_command('calculate-summation',   f"{_('Column')}: {get_title_from_layout('calculate-summation')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-minimum',     f"{_('Column')}: {get_title_from_layout('calculate-minimum')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-maximum',     f"{_('Column')}: {get_title_from_layout('calculate-maximum')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-median',      f"{_('Column')}: {get_title_from_layout('calculate-median')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-average',     f"{_('Column')}: {get_title_from_layout('calculate-average')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-standard-'
                       'deviation',             f"{_('Column')}: {get_title_from_layout('calculate-standard-deviation')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('count-values',          f"{_('Column')}: {get_title_from_layout('count-values')}...")
        create_command('count-distinct-values', f"{_('Column')}: {get_title_from_layout('count-distinct-values')}...")

        create_command('column-standard',       '$placeholder',
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-addition',    f"{_('Column')}: {get_title_from_layout('calculate-addition')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-'
                       'multiplication',        f"{_('Column')}: {get_title_from_layout('calculate-multiplication')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-subtraction', f"{_('Column')}: {get_title_from_layout('calculate-subtraction')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-division',    f"{_('Column')}: {get_title_from_layout('calculate-division')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-integer-'
                       'division',              f"{_('Column')}: {get_title_from_layout('calculate-integer-division')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-modulo',      f"{_('Column')}: {get_title_from_layout('calculate-modulo')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-percentage',  f"{_('Column')}: {get_title_from_layout('calculate-percentage')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-percent-of',  f"{_('Column')}: {get_title_from_layout('calculate-percent-of')}...",
                                                context = 'table_focus and numeric_focus')

        create_command('column-scientific',     '$placeholder',
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-absolute',    f"{_('Column')}: {get_title_from_layout('calculate-absolute')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-square-root', f"{_('Column')}: {get_title_from_layout('calculate-square-root')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-square',      f"{_('Column')}: {get_title_from_layout('calculate-square')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-cube',        f"{_('Column')}: {get_title_from_layout('calculate-cube')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-power-k',     f"{_('Column')}: {get_title_from_layout('calculate-power-k')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-exponent',    f"{_('Column')}: {get_title_from_layout('calculate-exponent')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-base-10',     f"{_('Column')}: {get_title_from_layout('calculate-base-10')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-natural',     f"{_('Column')}: {get_title_from_layout('calculate-natural')}...",
                                                context = 'table_focus and numeric_focus')

        create_command('column-trigonometry',   '$placeholder',
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-sine',        f"{_('Column')}: {get_title_from_layout('calculate-sine')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-cosine',      f"{_('Column')}: {get_title_from_layout('calculate-cosine')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-tangent',     f"{_('Column')}: {get_title_from_layout('calculate-tangent')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-arcsine',     f"{_('Column')}: {get_title_from_layout('calculate-arcsine')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-arccosine',   f"{_('Column')}: {get_title_from_layout('calculate-arccosine')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-arctangent',  f"{_('Column')}: {get_title_from_layout('calculate-arctangent')}...",
                                                context = 'table_focus and numeric_focus')

        create_command('round-value',           f"{_('Column')}: {get_title_from_layout('round-value')}...",
                                                context = 'table_focus and numeric_focus')

        create_command('column-information',   '$placeholder',
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-is-even',     f"{_('Column')}: {get_title_from_layout('calculate-is-even')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('calculate-is-odd',      f"{_('Column')}: {get_title_from_layout('calculate-is-odd')}...",
                                                context = 'table_focus and numeric_focus')
        create_command('extract-value-sign',    f"{_('Column')}: {get_title_from_layout('extract-value-sign')}...",
                                                context = 'table_focus and numeric_focus')

    def set_data(self,
                 tables: Tables = {},
                 sparse: Sparse = {},
                 ) ->    None:
        """"""
        # Remove existing document widgets
        widgets = self.document.widgets
        for widgets in widgets.values():
            for widget in widgets:
                widget.unparent()

        # Get cached dataframes by query plan
        cache_hits = []
        for index, (tname, (coord, table)) in enumerate(tables.items()):
            if not isinstance(table, LazyFrame):
                continue
            query_plan = table.serialize()
            for t in self.document.tables:
                if t.query_plan == query_plan:
                    tables[tname] = (coord, t.content)
                    cache_hits.append((index, query_plan))
                    break

        # Clean up the old tables
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

        if self.node:
            for tname, (coord, table) in tables.items():
                # Find the related node content
                contents = self.node.contents[1:-1]
                for content in contents:
                    box = content.Widget
                    label = box.get_first_child()
                    label = label.get_label()
                    if label == tname:
                        break

                # Find the pair socket and node
                self_content = content
                self_socket  = self_content.Socket
                link         = self_socket.links[0]
                pair_socket  = link.in_socket
                pair_node    = pair_socket.Frame

                # Collect sorted column names
                if pair_node.parent.action == 'sort-rows':
                    columns = []
                    for value in pair_node.do_save():
                        columns.append(value[0])
                    self.document.sorted[tname] = columns

                # Collect filtered column names
                if pair_node.parent.action == 'filter-rows':
                    columns = []
                    for value in pair_node.do_save():
                        columns.append(value[1])
                    self.document.filtered[tname] = columns

        def refresh_ui() -> None:
            """"""
            c_cell = self.selection.current_cursor_cell
            c_lcol = self.display.get_lcolumn_from_column(c_cell.column)
            c_lrow = self.display.get_lrow_from_row(c_cell.row)

            c_cell_name = self.display.get_cell_name_from_position(c_lcol, c_lrow)
            a_cell_name = self.selection.current_cell_name

            self.selection.update_from_name(f'{c_cell_name}:{a_cell_name}')

            self.selection.previous_cell_name = ''

            self.refresh_ui()

        def do_finish(table: DataTable) -> None:
            """"""
            if self.adjust_columns:
                self._adjust_column_widths_by_table(table)

            refresh_ui()

        # Setup tables
        for tname, (coord, table) in tables.items():
            table_index = self.document.create_table(table,
                                                     with_header = True,
                                                     column      = coord[0],
                                                     row         = coord[1],
                                                     table_name  = tname,
                                                     prefer_sync = self.prefer_synchro,
                                                     on_finish   = do_finish)

            if self.adjust_columns:
                table = self.document.tables[table_index]
                self._adjust_column_widths_by_table(table)

        # Setup sparse
        for coord, value in sparse.items():
            self.document.create_or_update_sparse(value,
                                                  column = coord[0],
                                                  row    = coord[1])

            if self.adjust_columns:
                self._adjust_column_widths_by_value(value, coord[0])

        # Flag the new table instances from cache
        for (index, query_plan) in cache_hits:
            table = self.document.tables[index]
            table.query_plan = query_plan

        self.Canvas.cleanup() # invalidate render caches

        cell_name = self.selection.current_cell_name or 'A1'
        self.selection.update_from_name(cell_name)

        self.selection.previous_cell_name = ''

        GLib.idle_add(self.refresh_ui)

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
        font_desc = f'Monospace Normal Regular {self.display.FONT_SIZE}px'
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

    def update_formula_bar(self) -> None:
        """"""
        from datetime import timedelta

        from ...core.utils import print_timedelta

        table = self._get_active_table_context(with_column = False)

        cell_data = self.selection.current_cell_data

        if table is not None and table.error_message:
            cell_data = table.error_message

        cell_data = '' if cell_data is None else cell_data

        # We don't natively support object types, but in any case the user has perfomed
        # an operation that returned an object, we want to show it properly in minimal.
        if isinstance(cell_data, timedelta):
            cell_data = print_timedelta(cell_data)

        cell_name  = self.selection.current_cell_name
        cell_data  = str(cell_data)
        cell_dtype = self.selection.current_cell_dtype

        if table is not None:
            if table.placeholder:
                cell_dtype = ''
            if table.error_message:
                cell_dtype = 'Error'

        parameter = GLib.Variant('as', [cell_name, cell_data, cell_dtype])
        self.activate_action('formula.update-formula-bar', parameter)

    def _adjust_column_widths_by_table(self,
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
        max_width = monitor.get_geometry().width // 8
        sample_data = table.head(50).vstack(table.tail(50))

        context = self.Canvas.get_pango_context()
        font_desc = context.get_font_description()
        font_family = font_desc.get_family() if font_desc else 'Sans'
        font_desc = f'{font_family} Normal Regular {self.display.FONT_SIZE}px #tnum=1'
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

        l_margin = 0
        r_margin = 0
        if table.width and table.height:
            from .widgets import SheetColumnDType
            from .widgets import SheetTableFilter
            l_margin += SheetColumnDType.WIDTH - 5
            r_margin += SheetTableFilter.WIDTH - 2

        for col_index, col_name in enumerate(table.columns):
            # Add table position offset into account
            col_index += table.bounding_box.column - 1

            # Compute text width of table header
            layout.set_text(col_name, -1)
            text_width = layout.get_pixel_size()[0]
            column_width = text_width + 2 * self.display.DEFAULT_CELL_PADDING
            column_width = column_width + l_margin + r_margin
            column_width = min(max_width, int(column_width))
            column_width = max(self.display.DEFAULT_CELL_WIDTH, column_width)
            self.display.column_widths[col_index] = column_width

            if table.height == 0:
                continue

            # Find longest table content
            try:
                expr = col(col_name).cast(String).fill_null('[Blank]')
                sample_text = sample_data.with_columns(expr)

                expr = col(col_name).str.len_chars().max()
                max_length = sample_text.select(expr).item()

                expr = col(col_name).str.len_chars() == max_length
                expr = when(expr).then(col(col_name)) \
                                 .otherwise(None) \
                                 .alias('$sample-text')
                sample_text = sample_text.with_columns(expr) \
                                         .drop_nulls('$sample-text') \
                                         .head(1) \
                                         .item(0, '$sample-text')
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

    def _adjust_column_widths_by_value(self,
                                       value:  Any,
                                       column: int,
                                       ) ->    None:
        """"""
        from gi.repository import Pango
        from polars import concat
        from polars import Series

        monitor = Gdk.Display.get_default().get_monitors()[0]
        max_width = monitor.get_geometry().width // 8

        context = self.Canvas.get_pango_context()
        font_desc = context.get_font_description()
        font_family = font_desc.get_family() if font_desc else 'Sans'
        font_desc = f'{font_family} Normal Regular {self.display.FONT_SIZE}px #tnum=1'
        font_desc = Pango.font_description_from_string(font_desc)

        layout = Pango.Layout.new(context)
        layout.set_wrap(Pango.WrapMode.NONE)
        layout.set_font_description(font_desc)

        n_column_widths = len(self.display.column_widths)

        # Initialize with default column widths
        if n_column_widths == 0:
            default_column_widths = [self.display.DEFAULT_CELL_WIDTH] * column
            self.display.column_widths = Series(default_column_widths, dtype = UInt32)
            n_column_widths = len(self.display.column_widths)

        # Expand with default column widths
        if n_column_widths < column:
            n_missing = column - n_column_widths
            default_column_widths = [self.display.DEFAULT_CELL_WIDTH] * n_missing
            default_column_widths = Series(default_column_widths, dtype = UInt32)
            self.display.column_widths = concat([self.display.column_widths,
                                                 default_column_widths])

            # Compute the width of the text
            current_column_width = self.display.column_widths[column - 1]
            layout.set_text(value, -1)
            text_width = layout.get_pixel_size()[0]
            column_width = text_width + 2 * self.display.DEFAULT_CELL_PADDING
            column_width = min(max_width, int(column_width))
            column_width = max(current_column_width, column_width)
            self.display.column_widths[column - 1] = column_width

        self.display.ccolumn_widths = Series(self.display.column_widths).cum_sum()

    def _transform_table(self,
                         func_name: str,
                         func_args: list[Any] = [],
                         ) ->       None:
        """"""
        table, column_name = self._get_active_table_context()

        if not isinstance(table, DataTable):
            return False

        window = self.get_root()

        def do_transform(func_args: list[Any] = [],
                         **kwargs:  dict,
                         ) ->       bool:
            """"""
            window.history.grouping = True
            self._insert_transformer_node(func_name, func_args, table)
            window.history.grouping = False
            self.grab_focus()

        from .ui.transform_layout import get_layout
        win_title, win_layout = get_layout(func_name)

        if len(win_layout) == 0:
            return do_transform(func_args)

        if not isinstance(win_layout, list):
            win_layout = [win_layout]

        column_strings  = [col for col in table.columns if table[col].dtype == String]
        column_floats   = [col for col in table.columns if table[col].dtype in FLOAT_TYPES]
        column_integers = [col for col in table.columns if table[col].dtype in INTEGER_TYPES]
        column_numerics = column_floats + column_integers

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
                    if var == '$numeric-columns':
                        rows[ridx][-1] = column_numerics

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

        subtitle = f'{table.tname} @ {self.title}'

        application = window.get_application()

        from .ui.transform_window import SheetTransformWindow
        dialog = SheetTransformWindow(title         = win_title,
                                      subtitle      = subtitle,
                                      layout        = win_layout,
                                      callback      = do_transform,
                                      transient_for = window,
                                      application   = application)
        dialog.present()

    def _filter_rows(self) -> None:
        """"""
        table = self._get_active_table_context(with_column = False)

        table_schema = table.collect_schema()

        if not isinstance(table, DataTable):
            return False

        window = self.get_root()

        def do_transform(func_args: list[Any] = [],
                         **kwargs:  dict,
                         ) ->       bool:
            """"""
            window.history.grouping = True
            self._insert_transformer_node('filter-rows', func_args, table)
            window.history.grouping = False
            self.grab_focus()

        subtitle = f'{table.tname} @ {self.title}'

        application = window.get_application()

        from .ui.filter_rows_window import SheetFilterRowsWindow
        dialog = SheetFilterRowsWindow(subtitle      = subtitle,
                                       table_schema  = table_schema,
                                       callback      = do_transform,
                                       transient_for = window,
                                       application   = application)
        dialog.present()

    def _join_tables(self) -> None:
        """"""
        table = self._get_active_table_context(with_column = False)

        if not isinstance(table, DataTable):
            return False

        window = self.get_root()
        editor = window.node_editor

        tables = self.get_all_tables()

        def do_join(func_args: list[Any] = [],
                    **kwargs:  dict,
                    ) ->       bool:
            """"""
            ltname, lcolumn, lcolumns, \
            rtname, rcolumn, rcolumns, \
            how, order = func_args

            window.history.grouping = True

            # Find all the pair nodes
            sheet1 = self._find_sheet_node_by_address(ltname)
            sheet2 = self._find_sheet_node_by_address(rtname)
            viewer = self._find_active_viewer_node()

            ltname = ltname.split(' @ ')[0]
            rtname = rtname.split(' @ ')[0]
            func_args = [ltname, lcolumn, lcolumns,
                         rtname, rcolumn, rcolumns,
                         how, order]

            # Create a new sheet node
            x = viewer.x - 175 - 50
            y = viewer.y
            sheet3 = editor.create_new_node('new-sheet', x, y)
            editor.add_node(sheet3)

            # Create a new joiner node
            x = sheet3.x - 175 - 50
            y = sheet3.y
            joiner = editor.create_new_node('join-tables', x, y)
            joiner.set_data(*func_args)
            editor.add_node(joiner)
            editor.select_by_click(joiner)

            # Connect all the pair nodes from/to the joiner node
            content = joiner.contents[3]
            editor.add_link(content.Socket, sheet1.contents[0].Socket)
            content = joiner.contents[4]
            editor.add_link(content.Socket, sheet2.contents[0].Socket)
            content = joiner.contents[0]
            editor.add_link(content.Socket, sheet3.contents[-1].Socket)
            content = sheet3.contents[0]
            editor.add_link(content.Socket, viewer.contents[-1].Socket)

            editor.auto_arrange(viewer)

            window.history.grouping = False

            self.grab_focus()

        tname = f'{table.tname} @ {self.title}'

        application = window.get_application()

        from .ui.join_tables_window import SheetJoinTablesWindow
        dialog = SheetJoinTablesWindow(tname         = tname,
                                       tables        = tables,
                                       callback      = do_join,
                                       transient_for = window,
                                       application   = application)
        dialog.present()

    def get_all_tables(self) -> list:
        """"""
        if not self.node:
            return []

        from ..node.factory import NodeSheet

        viewer = self._find_active_viewer_node()

        tables = []

        # Collect all tables in this sheet
        if not viewer:
            for table in self.document.tables:
                label = f'{table.tname} @ {self.title}'
                tables.append((label, table))
            return tables

        # Collect all tables visible to the viewer
        for content in viewer.contents[:-1]:
            link = content.Socket.links[0]
            node = link.in_socket.Frame
            if not isinstance(node.parent, NodeSheet):
                continue
            if not content.Page:
                continue
            title = content.Widget.get_label()
            editor = content.Page.get_child()
            for table in editor.document.tables:
                label = f'{table.tname} @ {title}'
                tables.append((label, table))

        return tables

    def _find_sheet_node_by_address(self,
                                    address: str,
                                    ) ->     NodeFrame:
        """"""""
        from ..node.factory import NodeSheet

        viewer = self._find_active_viewer_node()

        tname, sname = address.split(' @ ')

        for content in viewer.contents[:-1]:
            link = content.Socket.links[0]
            node = link.in_socket.Frame
            if not isinstance(node.parent, NodeSheet):
                continue
            if not content.Page:
                continue
            title = content.Widget.get_label()
            if title != sname:
                continue
            editor = content.Page.get_child()
            for table in editor.document.tables:
                if table.tname == tname:
                    return node

        return None

    def _find_active_viewer_node(self) -> NodeFrame:
        """"""
        from ..node.factory import NodeViewer

        content = self.node.contents[0]
        links = content.Socket.links
        for link in links:
            node = link.out_socket.Frame
            if not isinstance(node.parent, NodeViewer):
                continue
            if not node.is_active():
                continue
            return node

        return None

    def _write_custom_formula(self) -> None:
        """"""
        table = self._get_active_table_context(with_column = False)

        if not isinstance(table, DataTable):
            return False

        window = self.get_root()

        def do_transform(formula: str) -> None:
            """"""
            window.history.grouping = True
            self._insert_transformer_node('custom-formula', [formula], table)
            window.history.grouping = False
            self.grab_focus()

        application = window.get_application()

        subtitle = f'{table.tname} @ {self.title}'

        from ...ui.formula_editor.widget import FormulaEditorWindow
        editor_window = FormulaEditorWindow(subtitle      = subtitle,
                                            callback      = do_transform,
                                            transient_for = window,
                                            application   = application)
        editor_window.present()

    def _add_new_workspace(self,
                           name: str,
                           ) ->  None:
        """"""
        from ..node.factory import NodeViewer

        window = self.get_root()
        editor = window.node_editor

        window.history.grouping = True

        # Find the current active viewer node
        viewer = None
        for node in editor.nodes:
            if isinstance(node.parent, NodeViewer) and node.is_active():
                viewer = node
                break

        # Create a new sheet node
        position = (viewer.x - 175 - 50, viewer.y)
        sheet = editor.create_new_node(name, *position)
        if sheet:
            editor.add_node(sheet)
            editor.select_by_click(sheet)

        # Link the sheet to the viewer node
        in_socket = sheet.contents[0].Socket
        out_socket = viewer.contents[-1].Socket
        editor.add_link(in_socket, out_socket)

        editor.auto_arrange(viewer)

        window.history.grouping = False

    def _quick_sort_rows(self,
                         action:    Gio.SimpleAction,
                         parameter: GLib.Variant,
                         ) ->       None:
        """"""
        table, column_name = self._get_active_table_context()

        direction = parameter.get_string()

        if not isinstance(table, DataTable):
            return False

        window = self.get_root()
        editor = window.node_editor

        window.history.grouping = True

        # Find the related node content
        contents = self.node.contents[1:-1]
        for content in contents:
            box = content.Widget
            label = box.get_first_child()
            label = label.get_label()
            if label == table.tname:
                break

        # Find the pair node and socket
        self_content = content
        self_socket  = self_content.Socket
        link         = self_socket.links[0]
        pair_socket  = link.in_socket
        pair_node    = pair_socket.Frame

        # Modify the existing node
        if pair_node.parent.action == 'sort-rows':
            old_values = pair_node.do_save()
            new_values = deepcopy(old_values)

            for value in new_values:
                if value[0] == column_name:
                    new_values.remove(value)
                    break

            new_values.append([column_name, direction])

            from ..node.actions import ActionEditNode
            values = (old_values, new_values)
            action = ActionEditNode(editor, pair_node, values)
            window.do(action)

        # Create a new appropriate node
        else:
            func_args = [[[column_name, direction]]]
            self._insert_transformer_node('sort-rows', func_args, table)

        window.history.grouping = False

        self.grab_focus()

    def _clear_sort_rows(self,
                         action:    Gio.SimpleAction,
                         parameter: GLib.Variant,
                         ) ->       None:
        """"""
        table, column_name = self._get_active_table_context()

        if not isinstance(table, DataTable):
            return False

        window = self.get_root()
        editor = window.node_editor

        window.history.grouping = True

        # Find the related node content
        contents = self.node.contents[1:-1]
        for content in contents:
            box = content.Widget
            label = box.get_first_child()
            label = label.get_label()
            if label == table.tname:
                break

        # Find the pair socket and node
        self_content = content
        self_socket  = self_content.Socket
        link         = self_socket.links[0]
        pair_socket  = link.in_socket
        pair_node    = pair_socket.Frame

        # Modify the existing node
        if pair_node.parent.action == 'sort-rows':
            old_values = pair_node.do_save()
            new_values = deepcopy(old_values)

            for value in new_values:
                if value[0] == column_name:
                    new_values.remove(value)
                    break

            from ..node.actions import ActionEditNode
            values = (old_values, new_values)
            action = ActionEditNode(editor, pair_node, values)
            window.do(action)

        window.history.grouping = False

        self.grab_focus()

    def _quick_filter_rows(self,
                           values: Series,
                           ) ->    None:
        """"""
        table, column_name = self._get_active_table_context()

        if not isinstance(table, DataTable):
            return False

        func_args = []
        for value in values:
            func_args.append(['or', column_name, 'equals', value])

        window = self.get_root()
        window.history.grouping = True
        self._insert_transformer_node('filter-rows', func_args, table)
        window.history.grouping = False
        self.grab_focus()

    def _clear_filter_rows(self,
                           action:    Gio.SimpleAction,
                           parameter: GLib.Variant,
                           ) ->       None:
        """"""
        table, column_name = self._get_active_table_context()

        if not isinstance(table, DataTable):
            return False

        window = self.get_root()
        editor = window.node_editor

        window.history.grouping = True

        # Find the related node content
        contents = self.node.contents[1:-1]
        for content in contents:
            box = content.Widget
            label = box.get_first_child()
            label = label.get_label()
            if label == table.tname:
                break

        # Find the pair socket and node
        self_content = content
        self_socket  = self_content.Socket
        link         = self_socket.links[0]
        pair_socket  = link.in_socket
        pair_node    = pair_socket.Frame

        # Modify the existing node
        if pair_node.parent.action == 'filter-rows':
            old_values = pair_node.do_save()
            new_values = deepcopy(old_values)

            for value in old_values:
                if value[1] == column_name:
                    new_values.remove(value)

            from ..node.actions import ActionEditNode
            values = (old_values, new_values)
            action = ActionEditNode(editor, pair_node, values)
            window.do(action)

        window.history.grouping = False

        self.grab_focus()

    def _get_active_table_context(self,
                                  with_column: bool = True,
                                  ) ->         Any:
        """"""
        active = self.selection.current_active_cell

        lcolumn = self.display.get_lcolumn_from_column(active.column)
        lrow    = self.display.get_lrow_from_row(active.row)

        if with_column:
            return self.document.get_table_column_by_position(lcolumn, lrow)
        return self.document.get_table_by_position(lcolumn, lrow)

    def _insert_transformer_node(self,
                                 func_name: str,
                                 func_args: Any,
                                 table:     DataTable,
                                 ) ->       None:
        """"""
        window = self.get_root()
        editor = window.node_editor

        # Find the related node content
        contents = self.node.contents[1:-1]
        for content in contents:
            box = content.Widget
            label = box.get_first_child()
            label = label.get_label()
            if label == table.tname:
                break

        # Find the pair node and socket
        self_content = content
        self_socket  = self_content.Socket
        link         = self_socket.links[0]
        pair_socket  = link.in_socket
        pair_node    = pair_socket.Frame

        # Create a new appropriate node
        x = self.node.x - 175 - 50
        y = pair_node.y
        transformer = editor.create_new_node(func_name, x, y)
        transformer.set_data(*func_args)
        editor.add_node(transformer)
        editor.select_by_click(transformer)

        # Manipulate so that the transformer node seem to
        # be reconnected to the sheet node
        self_content.node_uid = id(transformer)

        data_key = next((k for k in ('value', 'table') if k in pair_node.data), '')
        keep_cache = bool(data_key)

        # Freeze pair node to prevent from rebuilding data
        # table from the source
        if keep_cache:
            pair_node.is_with_cache = True
            value = pair_node.data[data_key]
            pair_node.data[data_key] = table

        # Connect the pair node, new node, and self node
        content = transformer.contents[0]
        editor.add_link(content.Socket, self_socket)
        content = transformer.contents[1]
        editor.add_link(pair_socket, content.Socket)

        # Restore the pair node state
        if keep_cache:
            pair_node.is_with_cache = False
            pair_node.data[data_key] = value

        editor.auto_arrange(self.node)

from .canvas import SheetCanvas
from .display import SheetDisplay
from .document import SheetDocument
from .selection import SheetSelection
from .view import SheetView
