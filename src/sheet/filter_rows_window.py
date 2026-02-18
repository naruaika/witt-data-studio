# filter_rows_window.py
#
# Copyright (c) 2025 Naufan Rusyda Faikar
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

from polars import DataType
from gi.repository import Adw
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import Gtk
import datetime
import gc
import polars

from ..core.utils import isiterable

class SheetFilterRowData():

    def __init__(self,
                 clause: list,
                 index:  int,
                 ) ->    None:
        """"""
        self.clause = clause
        self.index  = index

    def get_data(self) -> str:
        """"""
        return self.clause[self.index]

    def set_data(self,
                 value: str,
                 ) ->   None:
        """"""
        self.clause[self.index] = value


@Gtk.Template(resource_path = '/com/wittara/studio/sheet/filter_rows_window.ui')
class SheetFilterRowsWindow(Adw.Window):

    __gtype_name__ = 'SheetFilterRowsWindow'

    WindowTitle      = Gtk.Template.Child()
    PreferencesPage  = Gtk.Template.Child()
    PreferencesGroup = Gtk.Template.Child()
    ApplyButton      = Gtk.Template.Child()

    def __init__(self,
                 subtitle:      str,
                 table_schema:  dict,
                 callback:      callable,
                 transient_for: Gtk.Window,
                 application:   Gtk.Application,
                 ) ->           None:
        """"""
        super().__init__(transient_for = transient_for,
                         application   = application)

        # Disable scroll to focus behavior of the Gtk.Viewport
        scrolled_window = self.PreferencesPage.get_first_child()
        viewport = scrolled_window.get_first_child()
        viewport.set_scroll_to_focus(False)

        # Make the window resize its height dynamically
        scrolled_window.set_min_content_height(362)
        scrolled_window.set_propagate_natural_height(True)

        box = self.PreferencesGroup.get_first_child()
        box = box.get_last_child()
        list_box = box.get_first_child()
        list_box.remove_css_class('boxed-list')
        list_box.add_css_class('boxed-list-separate')

        self.table_schema = table_schema
        self.callback     = callback
        self.clauses      = []

        self._create_list_item()

        # We set the maximum content height previously to prevent
        # the window from filling the entire user screen's height
        # but we don't want to prevent from manually resizing the
        # window to any size, so we reset the property here.
        GLib.idle_add(scrolled_window.set_min_content_height, -1)
        GLib.idle_add(scrolled_window.set_max_content_height, -1)

        # We set the window title after a delay so that the window
        # when displayed doesn't try to resize to fit the title in
        # case the title is too long
        GLib.idle_add(self.WindowTitle.set_subtitle, subtitle)

        controller = Gtk.EventControllerKey()
        controller.connect('key-pressed', self._on_key_pressed)
        self.add_controller(controller)

        self.ApplyButton.grab_focus()

    def _create_list_item(self) -> None:
        """"""
        dtype = next(iter(self.table_schema.values()))

        contents = [ # for new blank clause
            (
                'radio',
                {
                    'and': _('And'),
                    'or':  _('Or'),
                },
            ),
            (
                'column',
                {c: c for c in list(self.table_schema.keys())},
            ),
            (
                'operator',
                self._get_operators(dtype)
            ),
        ]

        def hide_first_grouper() -> None:
            """"""
            if len(self.clauses) == 0:
                return
            row = self.PreferencesGroup.get_row(0)
            header = row.get_first_child()
            suffixes = header.get_last_child()
            vbox = suffixes.get_first_child()
            hbox = vbox.get_first_child()
            hbox.set_visible(False)

        def add_list_item() -> None:
            """"""
            row = Adw.ActionRow()
            row.add_css_class('custom-row')
            self.PreferencesGroup.add(row)

            header = row.get_first_child()
            suffixes = header.get_last_child()
            title_box = suffixes.get_prev_sibling()
            title_box.set_visible(False)

            box = Gtk.Box(orientation   = Gtk.Orientation.VERTICAL,
                          spacing       = 6,
                          valign        = Gtk.Align.CENTER,
                          margin_top    = 8,
                          margin_bottom = 8)
            row.add_suffix(box)

            # For the grouper radio buttons
            subbox = Gtk.Box(hexpand = True)
            box.append(subbox)

            clause = []

            # Populate the new row with blank widgets
            for index, content in enumerate(contents):
                # Fill the data holder with default values
                _, options = content
                value = next(iter(options.keys()))
                clause.append(value)

                self._create_child_widget(clause, index, content, subbox)

                # For the column and operator dropdown buttons
                if index == 0:
                    subbox = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL,
                                     spacing     = 6,
                                     homogeneous = True,
                                     hexpand     = True)
                    box.append(subbox)

            self.clauses.append(clause)

            def on_delete_button_clicked(button: Gtk.Button) -> None:
                """"""
                self.PreferencesGroup.remove(row)
                index = next(i for i, x in enumerate(self.clauses) if x is clause)
                del self.clauses[index]
                hide_first_grouper()

            delete_button = Gtk.Button(icon_name     = 'user-trash-symbolic',
                                       margin_top    = 8,
                                       margin_bottom = 8)
            delete_button.add_css_class('circular')
            delete_button.add_css_class('error')
            delete_button.connect('clicked', on_delete_button_clicked)
            row.add_suffix(delete_button)

        add_button = Adw.ButtonRow(title           = f'{_('Add')} {_('Clause')}',
                                   start_icon_name = 'list-add-symbolic')
        self.PreferencesGroup.add(add_button)

        def on_add_button_clicked(button: Gtk.Button) -> None:
            """"""
            add_list_item()
            self.PreferencesGroup.remove(add_button)
            self.PreferencesGroup.add(add_button)
            hide_first_grouper()

        add_button.connect('activated', on_add_button_clicked)

        add_button.activate()

    def _create_child_widget(self,
                             clause:    list,
                             index:     int,
                             content:   tuple,
                             container: Gtk.Widget,
                             ) ->       SheetFilterRowData:
        """"""
        wtype = content
        if isiterable(wtype):
            wtype, options = wtype

        row_data = SheetFilterRowData(clause, index)

        match wtype:
            case 'column':
                set_data = lambda v: self._on_column_selected(row_data, v)
                widget = self._create_child_dropdown(row_data.get_data,
                                                     set_data,
                                                     options)
                container.append(widget)

            case 'operator':
                set_data = lambda v: self._on_operator_selected(row_data, v)
                widget = self._create_child_dropdown(row_data.get_data,
                                                     set_data,
                                                     options)
                container.append(widget)

            case 'date':
                widget = self._create_child_date(row_data.get_data,
                                                 row_data.set_data)
                container.append(widget)

            case 'time':
                widget = self._create_child_time(row_data.get_data,
                                                 row_data.set_data)
                container.append(widget)

            case 'datetime':
                widget = self._create_child_datetime(row_data.get_data,
                                                     row_data.set_data)
                container.append(widget)

            case 'dropdown':
                widget = self._create_child_dropdown(row_data.get_data,
                                                     row_data.set_data,
                                                     options)
                container.append(widget)

            case 'entry':
                widget = self._create_child_entry(row_data.get_data,
                                                  row_data.set_data)
                container.append(widget)

            case 'radio':
                widget = self._create_child_radio(row_data.get_data,
                                                  row_data.set_data,
                                                  options)
                container.append(widget)

        return row_data

    def _on_column_selected(self,
                            row_data: SheetFilterRowData,
                            value:    str,
                            ) ->      None:
        """"""
        row_data.set_data(value)

        dtype = self.table_schema[value]
        operators = self._get_operators(dtype)

        clause = row_data.clause
        index = next(i for i, x in enumerate(self.clauses) if x is clause)

        # Find the container where the operator widget is inside
        row = self.PreferencesGroup.get_row(index)
        header = row.get_first_child()
        suffixes = header.get_last_child()
        vbox = suffixes.get_first_child()
        hbox = vbox.get_first_child()
        hbox = hbox.get_next_sibling()

        # Remove the existing operator widget if exists
        dropdown = hbox.get_first_child()
        dropdown = dropdown.get_next_sibling()
        if dropdown:
            dropdown.unparent()

        # Create a new operator widget
        row_data = self._create_child_widget(clause    = clause,
                                             index     = 2,
                                             content   = ('operator', operators),
                                             container = hbox)

        # Reset the operator widget value if needed
        value = row_data.get_data()
        if value not in operators:
            value = next(iter(operators.keys()))

        # Trigger the operator widget signal handler
        # so that it'll create new subcontent widgets
        self._on_operator_selected(row_data, value)

    def _on_operator_selected(self,
                              row_data: SheetFilterRowData,
                              value:    str,
                              ) ->      None:
        """"""
        row_data.set_data(value)

        clause = row_data.clause
        index = next(i for i, x in enumerate(self.clauses) if x is clause)

        while len(clause) > 3:
            clause.pop()

        schemas = self._get_subcontents(value)

        # Find the container where the operator widget is inside
        row = self.PreferencesGroup.get_row(index)
        header = row.get_first_child()
        suffixes = header.get_last_child()
        vbox = suffixes.get_first_child()

        # Remove the subcontent container if exists
        hbox = vbox.get_first_child()
        hbox = hbox.get_next_sibling()
        container = hbox.get_next_sibling()
        if container:
            vbox.remove(container)

        if len(schemas) == 0:
            return

        container = Gtk.Box(orientation = Gtk.Orientation.VERTICAL,
                            spacing     = 6,
                            hexpand     = True)
        vbox.append(container)

        column_name = clause[1]
        dtype = self.table_schema[column_name]

        # Create new blank subcontent widgets
        for index, schema in enumerate(schemas):
            if isiterable(schema):
                __, options = schema
                default = next(iter(options.keys()))
                clause.append(default)

            if schema == ('entry'):
                match dtype:
                    case __ if dtype.is_integer():
                        clause.append(0)

                    case __ if dtype.is_numeric():
                        clause.append(0.0)

                    case __ if isinstance(dtype, polars.Datetime):
                        if value in {'is-in-the-next',
                                     'is-in-the-previous'}:
                            clause.append(0)
                            schema = ('entry')
                        else:
                            now = datetime.datetime.now()
                            clause.append(now)
                            schema = ('datetime')

                    case __ if dtype.is_(polars.Date):
                        if value in {'is-in-the-next',
                                     'is-in-the-previous'}:
                            clause.append(0)
                            schema = ('entry')
                        else:
                            today = datetime.date.today()
                            clause.append(today)
                            schema = ('date')

                    case __ if dtype.is_(polars.Time):
                        now = datetime.datetime.now()
                        now = datetime.time(now.hour,
                                            now.minute,
                                            now.second)
                        clause.append(now)
                        schema = ('time')

                    case __ if isinstance(dtype, polars.Duration):
                        clause.append(0)
                        schema = ('entry')

                    case __ if dtype.is_(polars.Boolean):
                        clause.append(True)
                        schema = (
                            'radio',
                            {
                                True:  _('True'),
                                False: _('False'),
                            },
                        )

                    case __:
                        clause.append('')

            self._create_child_widget(clause, index + 3, schema, container)

        should_link = value in {'is-between',
                                'is-not-between',
                                'is-in-the-next',
                                'is-in-the-previous'}

        if isinstance(dtype, polars.Datetime) and schemas == [('entry')]:
            container = container.get_first_child()
            should_link = True

        # Put some widgets inline to each other
        if should_link:
            container.set_orientation(Gtk.Orientation.HORIZONTAL)
            container.set_spacing(0)
            container.set_homogeneous(True)
            container.add_css_class('linked')

        gc.collect()

    def _get_operators(self,
                       dtype: DataType,
                       ) ->   dict:
        """"""
        operators = {
            'is-null':        _('Is Null'),
            'is-not-null':    _('Is Not Null'),
            'equals':         _('Equals'),
            'does-not-equal': _('Does Not Equal'),
        }

        if dtype.is_(polars.String):
            operators.update({
                'begins-with':         _('Begins With'),
                'does-not-begin-with': _('Does Not Begin With'),
                'ends-with':           _('Ends With'),
                'does-not-end-with':   _('Does Not End With'),
                'contains':            _('Contains'),
                'does-not-contain':    _('Does Not Contain'),
            })

        if dtype.is_numeric() or isinstance(dtype, polars.Duration):
            operators.update({
                'is-greater-than':             _('Is Greater Than'),
                'is-greater-than-or-equal-to': _('Is Greater Than or Equal To'),
                'is-less-than':                _('Is Less Than'),
                'is-less-than-or-equal-to':    _('Is Less Than or Equal To'),
                'is-between':                  _('Is Between'),
                'is-not-between':              _('Is Not Between'),
            })

        if dtype.is_numeric():
            operators.update({
                'above-average': _('Above Average'),
                'below-average': _('Below Average'),
            })

        if isinstance(dtype, polars.Datetime):
            operators.update({
                'is-before':             _('Is Before'),
                'is-before-or-equal-to': _('Is Before or Equal To'),
                'is-after':              _('Is After'),
                'is-after-or-equal-to':  _('Is After or Equal To'),
                'is-between':            _('Is Between'),
                'is-not-between':        _('Is Not Between'),
                'is-in-the-next':        _('Is in the Next'),
                'is-in-the-previous':    _('Is in the Previous'),
                'is-earliest':           _('Is Earliest'),
                'is-latest':             _('Is Latest'),
                'is-not-earliest':       _('Is Not Earliest'),
                'is-not-latest':         _('Is Not Latest'),
                'is-in-year':            _('Is in Year'),
                'is-in-quarter':         _('Is in Quarter'),
                'is-in-month':           _('Is in Month'),
                'is-in-week':            _('Is in Week'),
                'is-in-day':             _('Is in Day'),
            })

        if dtype.is_(polars.Date):
            operators.update({
                'is-before':             _('Is Before'),
                'is-before-or-equal-to': _('Is Before or Equal To'),
                'is-after':              _('Is After'),
                'is-after-or-equal-to':  _('Is After or Equal To'),
                'is-between':            _('Is Between'),
                'is-not-between':        _('Is Not Between'),
                'is-in-the-next':        _('Is in the Next'),
                'is-in-the-previous':    _('Is in the Previous'),
                'is-earliest':           _('Is Earliest'),
                'is-latest':             _('Is Latest'),
                'is-not-earliest':       _('Is Not Earliest'),
                'is-not-latest':         _('Is Not Latest'),
                'is-in-year':            _('Is in Year'),
                'is-in-quarter':         _('Is in Quarter'),
                'is-in-month':           _('Is in Month'),
                'is-in-week':            _('Is in Week'),
                'is-in-day':             _('Is in Day'),
            })

        if dtype.is_(polars.Time):
            operators.update({
                'is-greater-than':             _('Is Greater Than'),
                'is-greater-than-or-equal-to': _('Is Greater Than or Equal To'),
                'is-less-than':                _('Is Less Than'),
                'is-less-than-or-equal-to':    _('Is Less Than or Equal To'),
                'is-between':                  _('Is Between'),
                'is-earliest':                 _('Is Earliest'),
                'is-latest':                   _('Is Latest'),
                'is-not-earliest':             _('Is Not Earliest'),
                'is-not-latest':               _('Is Not Latest'),
            })

        return operators

    def _get_subcontents(self,
                         operator: str,
                         ) ->      list:
        """"""
        contents = {
            'equals':                      [('entry')],
            'does-not-equal':              [('entry')],

            'begins-with':                 [('entry')],
            'does-not-begin-with':         [('entry')],
            'ends-with':                   [('entry')],
            'does-not-end-with':           [('entry')],
            'contains':                    [('entry')],
            'does-not-contain':            [('entry')],

            'is-greater-than':             [('entry')],
            'is-greater-than-or-equal-to': [('entry')],
            'is-less-than':                [('entry')],
            'is-less-than-or-equal-to':    [('entry')],
            'is-between':                  [('entry'), ('entry')],
            'is-not-between':              [('entry'), ('entry')],

            'is-before':                   [('entry')],
            'is-before-or-equal-to':       [('entry')],
            'is-after':                    [('entry')],
            'is-after-or-equal-to':        [('entry')],
            'is-in-the-next':              [('entry'),
                                            ('dropdown', {'years':    _('Years'),
                                                          'quarters': _('Quarters'),
                                                          'months':   _('Months'),
                                                          'weeks':    _('Weeks'),
                                                          'days':     _('Days'),
                                                          'hours':    _('Hours'),
                                                          'minutes':  _('Minutes'),
                                                          'seconds':  _('Seconds')})],
            'is-in-the-previous':          [('entry'),
                                            ('dropdown', {'years':    _('Years'),
                                                          'quarters': _('Quarters'),
                                                          'months':   _('Months'),
                                                          'weeks':    _('Weeks'),
                                                          'days':     _('Days'),
                                                          'hours':    _('Hours'),
                                                          'minutes':  _('Minutes'),
                                                          'seconds':  _('Seconds')})],
            'is-in-year':                  [('dropdown', {'last-year':    _('Last Year'),
                                                          'this-year':    _('This Year'),
                                                          'next-year':    _('Next Year'),
                                                          'year-to-date': _('Year To Date')})],
            'is-in-quarter':               [('dropdown', {'last-quarter': _('Last Quarter'),
                                                          'this-quarter': _('This Quarter'),
                                                          'next-quarter': _('Next Quarter'),
                                                          'quarter-1':    _('Quarter 1'),
                                                          'quarter-2':    _('Quarter 2'),
                                                          'quarter-3':    _('Quarter 3'),
                                                          'quarter-4':    _('Quarter 4')})],
            'is-in-month':                 [('dropdown', {'last-month': _('Last Month'),
                                                          'this-month': _('This Month'),
                                                          'next-month': _('Next Month'),
                                                          'january':    _('January'),
                                                          'february':   _('February'),
                                                          'march':      _('March'),
                                                          'april':      _('April'),
                                                          'may':        _('May'),
                                                          'june':       _('June'),
                                                          'july':       _('July'),
                                                          'august':     _('August'),
                                                          'september':  _('September'),
                                                          'october':    _('October'),
                                                          'november':   _('November'),
                                                          'december':   _('December')})],
            'is-in-week':                  [('dropdown', {'last-week': _('Last Week'),
                                                          'this-week': _('This Week'),
                                                          'next-week': _('Next Week')})],
            'is-in-day':                   [('dropdown', {'yesterday': _('Yesterday'),
                                                          'today':     _('Today'),
                                                          'tomorrow':  _('Tomorrow')})],
        }

        if operator in contents:
            return contents[operator]
        return []

    def _create_child_date(self,
                           get_data: callable,
                           set_data: callable,
                           ) ->      Gtk.Entry:
        """"""
        from ..date_picker import DatePicker
        picker = DatePicker(halign            = Gtk.Align.CENTER,
                            show_week_numbers = True,
                            margin_top        = 5,
                            margin_bottom     = 5,
                            margin_start      = 5,
                            margin_end        = 5)
        popover = Gtk.Popover(child = picker)

        _get_data = lambda: get_data().strftime('%Y-%m-%d')

        def _set_data(value: str) -> None:
            """"""
            try:
                value = datetime.date.fromisoformat(value)
            except:
                entry.add_css_class('warning')
            else:
                entry.remove_css_class('warning')
                picker.set_year(value.year)
                picker.set_month(value.month - 1)
                picker.set_day(value.day)
                set_data(value)

        def on_icon_pressed(entry:    Gtk.Entry,
                            icon_pos: Gtk.EntryIconPosition,
                            ) ->      None:
            """"""
            if icon_pos == Gtk.EntryIconPosition.SECONDARY:
                rect = entry.get_icon_area(icon_pos)
                popover.set_pointing_to(rect)
                popover.popup()

        entry = self._create_child_entry(_get_data, _set_data)
        entry.set_icon_from_icon_name(icon_pos  = Gtk.EntryIconPosition.SECONDARY,
                                      icon_name = 'vcal-symbolic')
        entry.connect('icon-press', on_icon_pressed)

        def on_calendar_updated(widget: DatePicker) -> None:
            """"""
            value: datetime.date = get_data()
            value = value.replace(widget.get_year(),
                                  widget.get_month() + 1,
                                  widget.get_day())
            set_data(value)

            new_text = _get_data()
            if entry.get_text() != new_text:
                entry.remove_css_class('warning')
                entry.set_text(new_text)

            entry.grab_focus()

        picker.connect('day-selected', on_calendar_updated)
        picker.connect('next-month', on_calendar_updated)
        picker.connect('next-year', on_calendar_updated)
        picker.connect('prev-month', on_calendar_updated)
        picker.connect('prev-year', on_calendar_updated)

        popover.set_parent(entry)

        def on_entry_destroy(entry: Gtk.Entry) -> None:
            """"""
            popover.unparent()

        entry.connect('destroy', on_entry_destroy)

        return entry

    def _create_child_time(self,
                           get_data: callable,
                           set_data: callable,
                           ) ->      Gtk.Entry:
        """"""
        from ..time_picker import TimePicker
        picker = TimePicker(halign = Gtk.Align.CENTER,
                            valign = Gtk.Align.CENTER)
        popover = Gtk.Popover(child = picker)

        value: datetime.time = get_data()
        picker.set_hour(value.hour)
        picker.set_minute(value.minute)
        picker.set_second(value.second)

        _get_data = lambda: get_data().strftime('%H:%M:%S')

        def _set_data(value: str) -> None:
            """"""
            try:
                value = datetime.time.fromisoformat(value)
            except:
                entry.add_css_class('warning')
            else:
                entry.remove_css_class('warning')
                picker.set_hour(value.hour)
                picker.set_minute(value.minute)
                picker.set_second(value.second)
                set_data(value)

        def on_icon_pressed(entry:    Gtk.Entry,
                            icon_pos: Gtk.EntryIconPosition,
                            ) ->      None:
            """"""
            if icon_pos == Gtk.EntryIconPosition.SECONDARY:
                entry.grab_focus_without_selecting()
                picker.set_mode(picker.MODE_HOUR)
                picker.grab_focus()

                rect = entry.get_icon_area(icon_pos)
                popover.set_pointing_to(rect)
                popover.popup()

        entry = self._create_child_entry(_get_data, _set_data)
        entry.set_icon_from_icon_name(icon_pos  = Gtk.EntryIconPosition.SECONDARY,
                                      icon_name = 'clock-alt-symbolic')
        entry.connect('icon-press', on_icon_pressed)

        popover.set_parent(entry)

        def on_entry_destroy(entry: Gtk.Entry) -> None:
            """"""
            popover.unparent()

        entry.connect('destroy', on_entry_destroy)

        def on_closed(popover: Gtk.Popover) -> None:
            """"""
            entry.grab_focus()

        popover.connect('closed', on_closed)

        def on_time_updated(widget: TimePicker) -> None:
            """"""
            value: datetime.time = get_data()
            value = value.replace(widget.get_hour(),
                                  widget.get_minute(),
                                  widget.get_second())
            set_data(value)

            new_text = _get_data()
            if entry.get_text() != new_text:
                entry.remove_css_class('warning')
                entry.set_text(new_text)

            entry.grab_focus()

        picker.connect('time-updated', on_time_updated)

        return entry

    def _create_child_datetime(self,
                               get_data: callable,
                               set_data: callable,
                               ) ->      Gtk.Box:
        """"""
        default: datetime.datetime = get_data()

        box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL,
                      spacing     = 6,
                      hexpand     = True)

        current_date = default.date()
        current_time = default.time()

        def update_datetime() -> None:
            """"""
            try:
                new_datetime = datetime.datetime.combine(current_date,
                                                         current_time)
            except:
                return

            set_data(new_datetime)

        def get_date() -> datetime.date:
            """"""
            return current_date

        def set_date(new_date: datetime.date) -> None:
            """"""
            nonlocal current_date
            current_date = new_date
            update_datetime()

        def get_time() -> datetime.time:
            """"""
            return current_time

        def set_time(new_time: datetime.time) -> None:
            """"""
            nonlocal current_time
            current_time = new_time
            update_datetime()

        d = self._create_child_date(get_date, set_date)
        t = self._create_child_time(get_time, set_time)

        box.append(d)
        box.append(t)

        return box

    def _create_child_dropdown(self,
                               get_data: callable,
                               set_data: callable,
                               options:  dict,
                               ) ->      Gtk.DropDown:
        """"""
        dropdown = Gtk.DropDown(hexpand = True,
                                valign  = Gtk.Align.CENTER)

        def setup_factory(list_item_factory: Gtk.SignalListItemFactory,
                          list_item:         Gtk.ListItem,
                          ) ->               None:
            """"""
            box = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL,
                          hexpand     = True)
            list_item.set_child(box)

            label = Gtk.Label()
            box.append(label)

            image = Gtk.Image(opacity = 0)
            image.set_from_icon_name('object-select-symbolic')
            box.append(image)

            list_item.label = label
            list_item.image = image
            list_item.bind_item = None

        def bind_factory(list_item_factory: Gtk.SignalListItemFactory,
                         list_item:         Gtk.ListItem,
                         ) ->               None:
            """"""
            item_data = list_item.get_item()
            label = item_data.get_string()

            def do_select() -> bool:
                """"""
                is_selected = list_item.get_selected()
                list_item.image.set_opacity(is_selected)
                if is_selected:
                    dropdown.set_tooltip_text(label)
                return is_selected

            def on_selected(*args) -> None:
                """"""
                if do_select():
                    value = next((k for k, v in options.items() if v == label), None)
                    set_data(value)

            list_item.label.set_label(label)

            if list_item.bind_item:
                list_item.disconnect(list_item.bind_item)

            list_item.bind_item = dropdown.connect('notify::selected', on_selected)

            do_select()

        model = Gtk.StringList()
        for option in options.values():
            model.append(option)
        dropdown.set_model(model)

        list_factory = Gtk.SignalListItemFactory()
        list_factory.connect('setup', setup_factory)
        list_factory.connect('bind', bind_factory)
        dropdown.set_list_factory(list_factory)

        factory = Gtk.BuilderListItemFactory.new_from_bytes(None, GLib.Bytes.new(bytes(
"""
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <template class="GtkListItem">
    <property name="child">
      <object class="GtkLabel">
        <property name="halign">start</property>
        <property name="hexpand">true</property>
        <property name="ellipsize">end</property>
        <binding name="label">
          <lookup name="string" type="GtkStringObject">
            <lookup name="item">GtkListItem</lookup>
          </lookup>
        </binding>
      </object>
    </property>
  </template>
</interface>
""", 'utf-8')))
        dropdown.set_factory(factory)

        selected = next((i for i, key in enumerate(options) if key == get_data()), 0)
        dropdown.set_selected(selected)

        return dropdown

    def _create_child_entry(self,
                            get_data: callable,
                            set_data: callable,
                            ) ->      Gtk.Entry:
        """"""
        from ..core.arithmetic_evaluator import Evaluator
        evaluator = Evaluator()

        default = get_data()

        entry = Gtk.Entry(text    = str(default),
                          hexpand = True,
                          valign  = Gtk.Align.CENTER)

        if isinstance(default, (int, float)):
            entry.set_input_purpose(Gtk.InputPurpose.NUMBER)
        else:
            entry.set_placeholder_text(f'[{_('Empty')}]')

        def on_changed(entry: Gtk.Entry) -> None:
            """"""
            text = entry.get_text()
            try:
                if isinstance(default, (int, float)):
                    text = evaluator.evaluate(text)
                if isinstance(default, int):
                    text = int(text)
                if isinstance(default, float):
                    text = float(text)
            except:
                entry.add_css_class('warning')
            else:
                entry.remove_css_class('warning')
                set_data(text)

        entry.connect('changed', on_changed)

        return entry

    def _create_child_radio(self,
                            get_data: callable,
                            set_data: callable,
                            options:  dict,
                            ) ->      Gtk.Box:
        """"""
        box = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL,
                      homogeneous = True,
                      hexpand     = True)
        box.add_css_class('custom-linked')

        primary_button = None

        def on_toggled(check_button: Gtk.CheckButton) -> None:
            """"""
            if check_button.get_active():
                value = check_button.get_label()
                key = next((k for k, v in options.items() if v == value), None)
                set_data(key)

        for key, val in options.items():
            check_button = Gtk.CheckButton(label   = val,
                                           hexpand = True)
            check_button.add_css_class('custom-check')
            check_button.connect('toggled', on_toggled)
            box.append(check_button)

            if primary_button:
                check_button.set_group(primary_button)
            else:
                primary_button = check_button

            if key == get_data():
                check_button.set_active(True)

        return box

    @Gtk.Template.Callback()
    def _on_apply_button_clicked(self,
                                 button: Gtk.Button,
                                 ) ->    None:
        """"""
        self.close() # close first to properly handle the focus
        self.callback(self.clauses)

    def _on_input_activated(self,
                            widget: Gtk.Widget,
                            ) ->    None:
        """"""
        self._on_apply_button_clicked(self.ApplyButton)

    def _on_key_pressed(self,
                        event:   Gtk.EventControllerKey,
                        keyval:  int,
                        keycode: int,
                        state:   Gdk.ModifierType,
                        ) ->     bool:
        """"""
#       if keyval == Gdk.KEY_Escape:
#           self.close()
#           return Gdk.EVENT_STOP
        return Gdk.EVENT_PROPAGATE
