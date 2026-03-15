# table_filter.py
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

from gi.repository import Adw
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Graphene
from gi.repository import Gtk
from gi.repository import Pango
from polars import DataFrame
from polars import Series
import math

class SheetTableFilter(Gtk.Widget):

    __gtype_name__ = 'SheetTableFilter'

    WIDTH  = 22
    HEIGHT = 22

    x = 0
    y = 0

    def __init__(self,
                 x:        int,
                 y:        int,
                 column:   int,
                 row:      int,
                 sorted:   bool = False,
                 filtered: bool = False,
                 ) ->      None:
        """"""
        super().__init__(halign = Gtk.Align.CENTER,
                         valign = Gtk.Align.CENTER)

        self.set_size_request(self.WIDTH, self.HEIGHT)

        self.set_cursor(Gdk.Cursor.new_from_name('default'))

        self.x = x
        self.y = y

        self.column = column
        self.row    = row

        self.sorted   = sorted
        self.filtered = filtered

        self._being_hovered = False
        self._being_focused = False

        self._setup_controllers()

    def _setup_controllers(self) -> None:
        """"""
        controller = Gtk.EventControllerMotion()
        controller.connect('enter', self._on_entered)
        controller.connect('leave', self._on_left)
        self.add_controller(controller)

        controller = Gtk.GestureClick()
        controller.set_propagation_phase(Gtk.PropagationPhase.TARGET)
        controller.connect('released', self._on_released)
        self.add_controller(controller)

    def do_snapshot(self,
                    snapshot: Gtk.Snapshot,
                    ) ->      None:
        """"""
        style_manager = Adw.StyleManager.get_default()
        prefers_dark = style_manager.get_dark()

        x = -1
        y = +2

        bounds = Graphene.Rect().init(0, 0, self.WIDTH, self.HEIGHT)
        context = snapshot.append_cairo(bounds)

        active = self._being_hovered or self._being_focused

        # Draw the background fill
        if active:
            if prefers_dark:
                context.set_source_rgb(0.75, 0.75, 0.75)
                context.rectangle(x, y, self.WIDTH-1, self.HEIGHT-3)
                context.fill()
            else:
                context.set_source_rgb(0.25, 0.25, 0.25)
                context.rectangle(x, y, self.WIDTH-1, self.HEIGHT-3)
                context.fill()

        if (
            (prefers_dark and not active) or
            (not prefers_dark and active)
        ):
            context.set_source_rgb(1.0, 1.0, 1.0)
        else:
            context.set_source_rgb(0.0, 0.0, 0.0)

        context.set_hairline(True)

        if self.sorted or self.filtered:
            context.arc(self.WIDTH  / 2 - 1,
                        self.HEIGHT / 2 + 1,
                        3.0,
                        0,
                        2 * math.pi)
            context.fill()

        else:
            # Draw the left diagonal line
            start_x = x + 5
            start_y = y + 7
            end_x = x + self.WIDTH  / 2
            end_y = y + self.HEIGHT - 9
            context.move_to(start_x, start_y)
            context.line_to(end_x, end_y)

            # Draw the right diagonal line
            start_x = x + self.WIDTH  / 2
            start_y = y + self.HEIGHT - 9
            end_x = x + self.WIDTH - 5
            end_y = y + 7
            context.move_to(start_x, start_y)
            context.line_to(end_x, end_y)

            context.stroke()

    def _on_entered(self,
                    motion: Gtk.EventControllerMotion,
                    x:      float,
                    y:      float,
                    ) ->    None:
        """"""
        self._being_hovered = True
        self.queue_draw()

    def _on_left(self,
                 motion: Gtk.EventControllerMotion,
                 ) ->    None:
        """"""
        self._being_hovered = False
        self.queue_draw()

    def _on_released(self,
                     gesture: Gtk.GestureClick,
                     n_press: int,
                     x:       float,
                     y:       float,
                     ) ->     None:
        """"""
        canvas = self.get_parent()
        editor = canvas.get_editor()

        table, column_name = editor.document.get_table_column_by_position(self.column, self.row)
        series = table.get_column(column_name)

        popover = SheetTabelFilterMenu(series, editor)

        self._setup_popover_menu(popover)

        self._being_focused = True
        self.queue_draw()

        popover.popup()

    def _setup_popover_menu(self,
                            popover: Gtk.PopoverMenu,
                            ) ->     None:
        """"""
        canvas = self.get_parent()
        popover.set_parent(canvas)

        rect = Gdk.Rectangle()
        rect.x = self.x + self.WIDTH / 2 - 1
        rect.y = self.y + self.HEIGHT - 2
        rect.width  = 1
        rect.height = 1
        popover.set_pointing_to(rect)

        def on_closed(popover: Gtk.PopoverMenu) -> None:
            """"""
            self._being_focused = False
            self.queue_draw()

        popover.connect('closed', on_closed)

        self._setup_menu_items(popover)

    def _setup_menu_items(self,
                          popover: Gtk.PopoverMenu,
                          ) ->     None:
        """"""
        menu = popover.get_menu_model()

        for s_index in range(menu.get_n_items()):
            section = menu.get_item_link(s_index, 'section')

            if section is None:
                continue

            for i_index in range(section.get_n_items()):
                action = section.get_item_attribute_value(i_index, 'action', None)

                if not action:
                    continue

                action = action.get_string()

                if (
                    (action == 'sheet.clear-sort-rows'   and not self.sorted) or
                    (action == 'sheet.clear-filter-rows' and not self.filtered)
                ):
                    action = action + ':disabled'

                item = Gio.MenuItem.new_from_model(section, i_index)
                item.set_attribute_value('action', GLib.Variant.new_string(action))

                section.remove(i_index)
                section.insert_item(i_index, item)



class SheetTableFilterListItem(GObject.Object):

    __gtype_name__ = 'SheetTableFilterListItem'

    index        = GObject.Property(type = int,  default = 0)
    count        = GObject.Property(type = int,  default = 0)
    value        = GObject.Property(type = str,  default = '')
    active       = GObject.Property(type = bool, default = True)
    inconsistent = GObject.Property(type = bool, default = False)

    def __init__(self,
                 index:        int  = 0,
                 count:        int  = 0,
                 value:        str  = '',
                 active:       bool = True,
                 inconsistent: bool = False,
                 ) ->    None:
        """"""
        super().__init__()

        self.index        = index
        self.count        = count
        self.value        = value
        self.active       = active
        self.inconsistent = inconsistent



FILTER_PAGE_SIZE = 1_000
_filter_list_items_pool = []
for i in range(FILTER_PAGE_SIZE):
    _filter_list_items_pool.append(SheetTableFilterListItem())



@Gtk.Template(resource_path = '/com/wittara/studio/editors/sheet/widgets/table_filter.ui')
class SheetTabelFilterMenu(Gtk.PopoverMenu):

    __gtype_name__ = 'SheetTableFilterMenu'

    FilterSearchBox      = Gtk.Template.Child()
    FilterSearchEntry    = Gtk.Template.Child()
    FilterUseRegExp      = Gtk.Template.Child()
    FilterListView       = Gtk.Template.Child()
    FilterScrolledWindow = Gtk.Template.Child()
    FilterSelection      = Gtk.Template.Child()
    FilterListStore      = Gtk.Template.Child()
    FilterStatus         = Gtk.Template.Child()

    def __init__(self,
                 series: 'Series',
                 editor: 'SheetEditor',
                 ) ->    'None':
        """"""
        super().__init__()

        self.editor = editor

        self._setup_controllers()
        self._setup_actions()

        from threading import Thread
        thread = Thread(target = self._setup_uinterfaces,
                        args = [series],
                        daemon = True)
        thread.start()

    def _setup_uinterfaces(self,
                           series: Series,
                           ) ->    None:
        """"""
        self.value_counts = series.rename('value') \
                                  .value_counts(parallel = True) \
                                  .sort('value') \
                                  .with_columns(active = True) \
                                  .with_row_index()
        self.curr_vcounts = self.value_counts.clone()

        self._is_toggling = False

        self.populate_filter_list_items()

    def _setup_controllers(self) -> None:
        """"""
        factory = Gtk.SignalListItemFactory()
        factory.connect('setup', self._setup_filter_factory)
        factory.connect('bind', self._bind_filter_factory)
        factory.connect('unbind', self._unbind_filter_factory)
        self.FilterListView.set_factory(factory)

        def on_closed(popover: Gtk.PopoverMenu) -> None:
            """"""
            self.FilterSelection.set_model(None)
            GLib.timeout_add(250, popover.unparent)

        self.connect('closed', on_closed)

    def _setup_actions(self) -> None:
        """"""
        group = Gio.SimpleActionGroup.new()
        self.insert_action_group('sheet', group)

        def create_action(name:       str,
                          callback:   callable,
                          param_type: GLib.VariantType = None,
                          ) ->        None:
            """"""
            action = Gio.SimpleAction.new(name, param_type)
            action.connect('activate', callback)
            group.add_action(action)

        create_action('quick-filter-rows', lambda *_: self._quick_filter_rows())

    def _setup_filter_factory(self,
                              list_item_factory: Gtk.SignalListItemFactory,
                              list_item:         Gtk.ListItem,
                              ) ->               None:
        """"""
        check_button = Gtk.CheckButton(active = True)
        list_item.set_child(check_button)

        box = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL,
                      spacing     = 10)
        check_button.set_child(box)

        vlabel = Gtk.Label(ellipsize = Pango.EllipsizeMode.END,
                           hexpand   = True,
                           xalign    = 0.0)
        box.append(vlabel)

        clabel = Gtk.Label()
        clabel.add_css_class('dimmed')
        clabel.add_css_class('numeric')
        box.append(clabel)

        list_item.hactive = None
        list_item.hincons = None

    def _bind_filter_factory(self,
                             list_item_factory: Gtk.SignalListItemFactory,
                             list_item:         Gtk.ListItem,
                             ) ->               None:
        """"""
        item_data = list_item.get_item()

        check_button = list_item.get_child()
        box = check_button.get_child()

        value = str(item_data.value)
        vlabel = box.get_first_child()
        vlabel.set_label(value)
        vlabel.set_tooltip_text(value)

        attrs = Pango.AttrList()
        if hasattr(item_data, 'alias'):
            attr = Pango.attr_style_new(Pango.Style.ITALIC)
            attrs.insert(attr)
        vlabel.set_attributes(attrs)

        count = str(item_data.count)
        clabel = box.get_last_child()
        clabel.set_label(count)

        self._is_toggling = True
        list_item.hactive = item_data.bind_property('active',
                                                    check_button,
                                                    'active',
                                                    GObject.BindingFlags.SYNC_CREATE)
        list_item.hincons = item_data.bind_property('inconsistent',
                                                    check_button,
                                                    'inconsistent',
                                                    GObject.BindingFlags.SYNC_CREATE)
        self._is_toggling = False

        check_button.connect('toggled', self._on_filter_item_toggled, item_data)

    def _unbind_filter_factory(self,
                               list_item_factory: Gtk.SignalListItemFactory,
                               list_item:         Gtk.ListItem,
                               ) ->               None:
        """"""
        if list_item.hactive:
            list_item.hactive.unbind()
            list_item.hactive = None

        if list_item.hincons:
            list_item.hincons.unbind()
            list_item.hincons = None

    def _on_filter_item_toggled(self,
                                button:    Gtk.CheckButton,
                                item_data: SheetTableFilterListItem,
                                ) ->       None:
        """"""
        if self._is_toggling:
            return
        self._is_toggling = True

        from polars import col
        from polars import when

        active = button.get_active()

        if hasattr(item_data, 'alias'):
            value = item_data.alias
        else:
            value = self.value_counts['value'][item_data.index]

        if value == 'select-all':
            self.value_counts = self.value_counts.with_columns(active = active)
            self.curr_vcounts = self.curr_vcounts.with_columns(active = active)

            for idata in self.FilterListStore:
                if hasattr(idata, 'alias'):
                    if idata.alias in {'select-all',
                                       'select-all-results'}:
                        idata.inconsistent = False
                idata.active = active

            self._is_toggling = False

            return

        if value == 'select-all-results':
            expr = col('value').is_in(self.curr_vcounts['value'])
            expr = (
                when(expr)
                    .then(active)
                    .otherwise(col('active'))
                    .alias('active')
            )
            self.value_counts = self.value_counts.with_columns(expr)
            self.curr_vcounts = self.curr_vcounts.with_columns(active = active)

            for idata in self.FilterListStore:
                if hasattr(idata, 'alias'):
                    if idata.alias == 'select-all':
                        _active, consistent = self._is_all_active(self.value_counts)
                        idata.active = _active
                        idata.inconsistent = not consistent

                    if idata.alias == 'select-all-results':
                        idata.active = active
                        idata.inconsistent = False

                else:
                    idata.active = active

            self._is_toggling = False

            return

        expr = col('value').is_null() if value is None \
                                      else col('value') == value
        expr = (
            when(expr)
                .then(active)
                .otherwise(col('active'))
                .alias('active')
        )
        self.value_counts = self.value_counts.with_columns(expr)
        self.curr_vcounts = self.curr_vcounts.with_columns(expr)

        for idata in self.FilterListStore:
            if not hasattr(idata, 'alias'):
                break

            if idata.alias == 'select-all':
                _active, consistent = self._is_all_active(self.value_counts)
                idata.active = _active
                idata.inconsistent = not consistent

            if idata.alias == 'select-all-results':
                _active, consistent = self._is_all_active(self.curr_vcounts)
                idata.active = _active
                idata.inconsistent = not consistent

        self._is_toggling = False

    def populate_filter_list_items(self) -> None:
        """"""
        from polars import col
        from polars import String

        self.FilterListStore.remove_all()

        self.curr_vcounts = self.value_counts.clone()

        query = self.FilterSearchEntry.get_text()
        use_regexp = self.FilterUseRegExp.get_active()

        if query:
            expr = col('value').cast(String)
            if use_regexp:
                expr = expr.str.contains(f'(?i){query}')
            else:
                expr = expr.str.contains_any([query], ascii_case_insensitive = True)
            self.curr_vcounts = self.curr_vcounts.filter(expr)

        items_to_add = []

        if self.curr_vcounts.height:
            value = f'[{_('Select All')}]'
            n_rows = self.value_counts['count'].sum()
            active, consistent = self._is_all_active(self.value_counts)
            item = SheetTableFilterListItem(-1, n_rows, value, active)
            item.inconsistent = not consistent
            item.alias = 'select-all'
            items_to_add.append(item)

            if query:
                value = f'[{_('Select All Results')}]'
                n_rows = self.curr_vcounts['count'].sum()
                active, consistent = self._is_all_active(self.curr_vcounts)
                item = SheetTableFilterListItem(-1, n_rows, value, active)
                item.inconsistent = not consistent
                item.alias = 'select-all-results'
                items_to_add.append(item)

        i = 0
        for index, value, count, active in self.curr_vcounts.iter_rows():
            item = _filter_list_items_pool[i]
            item.index  = index
            item.value  = value
            item.count  = count
            item.active = active
            items_to_add.append(item)

            if hasattr(item, 'alias'):
                del item.alias

            if value is None:
                item.value = f'[{_('None')}]'
                item.alias = value

            if value == '':
                item.value = f'[{_('Empty')}]'
                item.alias = value

            i += 1
            if FILTER_PAGE_SIZE == i:
                break

        GLib.idle_add(self.FilterListStore.splice, 0, 0, items_to_add)

        if len(items_to_add) == 0:
            self.FilterStatus.set_label(_('No matching values'))
            GLib.idle_add(self.FilterStatus.set_visible, True)

        else:
            visible = FILTER_PAGE_SIZE < self.curr_vcounts.height

            if visible:
                self.FilterStatus.set_label(_('Showing up to 1,000 unique values'))

            GLib.idle_add(self.FilterStatus.set_visible, visible)

    def _is_all_active(self,
                       dataframe: DataFrame,
                       ) ->       tuple[bool, bool]:
        """"""
        from polars import col
        result = dataframe.select(
            active     = col('active').first(),
            consistent = col('active').n_unique() == 1,
        )
        active     = result['active'].item()
        consistent = result['consistent'].item()
        if not consistent:
            active = True
        return active, consistent

    @Gtk.Template.Callback()
    def _on_filter_search_entry_activated(self,
                                          entry: Gtk.Entry,
                                          ) ->   None:
        """"""
        self.populate_filter_list_items()

    @Gtk.Template.Callback()
    def _on_filter_regular_expression_toggled(self,
                                              button: Gtk.CheckButton,
                                              ) ->    None:
        """"""
        self.populate_filter_list_items()

    def _quick_filter_rows(self) -> None:
        """"""
        from polars import col
        values = self.value_counts.filter(col('active') == True) \
                                  .get_column('value')
        self.editor._quick_filter_rows(values)

from ..editor import SheetEditor
