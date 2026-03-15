# filter_builder.py
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
from gi.repository import Adw
from gi.repository import Gtk

from ....core.utils import isiterable

from .dropdown        import *
from .entry           import *
from .date_picker     import *
from .time_picker     import *
from .datetime_picker import *

class NodeFilterBuilder(Gtk.Box):

    __gtype_name__ = 'NodeFilterBuilder'

    def __init__(self,
                 get_data: callable,
                 set_data: callable,
                 tschema:  dict,
                 ) ->      None:
        """"""
        super().__init__(orientation = Gtk.Orientation.VERTICAL,
                         spacing     = 6)

        self.clauses: list = deepcopy(get_data())

        import datetime
        import gc
        import polars

        class ItemData():

            def __init__(self,
                         clauses: list,
                         clause:  list,
                         index:   int,
                         ) ->     None:
                """"""
                self.clauses = clauses
                self.clause  = clause
                self.index   = index

            def get_data(self) -> str:
                """"""
                return self.clause[self.index]

            def set_data(self,
                         value: str,
                         ) ->   None:
                """"""
                self.clause[self.index] = value
                set_data(deepcopy(self.clauses))

        def get_operators(dtype: polars.DataType) -> dict:
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

        def get_subcontents(operator: str) -> list:
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

        def create_child_widget(clause:    list,
                                index:     int,
                                content:   tuple,
                                container: Gtk.Widget,
                                ) ->       ItemData:
            """"""
            def on_operator_selected(row_data: ItemData,
                                     value:    str,
                                     ) ->      None:
                """"""
                index = next(i for i, x in enumerate(self.clauses) if x is row_data.clause)

                while len(row_data.clause) > 3:
                    row_data.clause.pop()

                schemas = get_subcontents(value)

                # Find the container where the operator widget is inside
                row = self.get_first_child()
                row_idx = 0
                while row_idx < index:
                    row = row.get_next_sibling()
                    row_idx += 1
                box = row.get_first_child()
                subbox = box.get_first_child()
                subbox = subbox.get_next_sibling()

                # Remove the subcontent container if exists
                container = subbox.get_next_sibling()
                if container:
                    box.remove(container)

                if len(schemas) == 0:
                    row_data.set_data(value)
                    return

                container = Gtk.Box(orientation = Gtk.Orientation.VERTICAL,
                                    hexpand     = True)
                container.add_css_class('linked')
                box.append(container)

                column_name = row_data.clause[1]
                dtype = tschema[column_name]

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

                    create_child_widget(clause, index + 3, schema, container)

                row_data.clause[row_data.index] = value
                set_data(deepcopy(self.clauses))

                gc.collect()

            def on_column_selected(row_data: ItemData,
                                   value:    str,
                                   ) ->      None:
                """"""
                row_data.set_data(value)

                dtype = tschema[value]
                operators = get_operators(dtype)

                index = next(i for i, x in enumerate(self.clauses) if x is row_data.clause)

                # Find the container where the operator widget is inside
                row = self.get_first_child()
                row_idx = 0
                while row_idx < index:
                    row = row.get_next_sibling()
                    row_idx += 1
                box = row.get_first_child()
                subbox = box.get_first_child()
                subbox = subbox.get_next_sibling()

                # Remove the existing operator widget if exists
                dropdown = subbox.get_first_child()
                dropdown = dropdown.get_next_sibling()
                if dropdown:
                    dropdown.unparent()

                # Create a new operator widget
                row_data = create_child_widget(clause    = row_data.clause,
                                               index     = 2,
                                               content   = ('operator', operators),
                                               container = subbox)

                # Reset the operator widget value if needed
                value = row_data.get_data()
                if value not in operators:
                    value = next(iter(operators.keys()))

                # Trigger the operator widget signal handler
                # so that it'll create new subcontent widgets
                on_operator_selected(row_data, value)

            def restore_subcontents(row_data: ItemData) -> None:
                """"""
                value = row_data.get_data()
                schemas = get_subcontents(value)

                if len(schemas) == 0:
                    return

                container = Gtk.Box(orientation = Gtk.Orientation.VERTICAL,
                                    hexpand     = True)
                container.add_css_class('linked')

                row = self.get_last_child()
                box = row.get_first_child()
                box.append(container)

                column_name = row_data.clause[1]
                dtype = tschema[column_name]

                for index, schema in enumerate(schemas):
                    if schema == ('entry'):
                        match dtype:
                            case __ if isinstance(dtype, polars.Datetime):
                                if value in {'is-in-the-next',
                                             'is-in-the-previous'}:
                                    schema = ('entry')
                                else:
                                    schema = ('datetime')

                            case __ if dtype.is_(polars.Date):
                                if value in {'is-in-the-next',
                                             'is-in-the-previous'}:
                                    schema = ('entry')
                                else:
                                    schema = ('date')

                            case __ if dtype.is_(polars.Time):
                                schema = ('time')

                            case __ if isinstance(dtype, polars.Duration):
                                schema = ('entry')

                            case __ if dtype.is_(polars.Boolean):
                                schema = (
                                    'radio',
                                    {
                                        True:  _('True'),
                                        False: _('False'),
                                    },
                                )

                    create_child_widget(row_data.clause, index + 3, schema, container)

            wtype = content
            if isiterable(wtype):
                wtype, options = wtype

            row_data = ItemData(self.clauses, clause, index)

            match wtype:
                case 'column':
                    widget = NodeDropdown(row_data.get_data,
                                          lambda v: on_column_selected(row_data, v),
                                          options)
                    container.append(widget)

                case 'operator':
                    widget = NodeDropdown(row_data.get_data,
                                          lambda v: on_operator_selected(row_data, v),
                                          options)
                    container.append(widget)

                    if self.is_restoring:
                        restore_subcontents(row_data)

                case 'date':
                    widget = NodeDatePicker(row_data.get_data,
                                            row_data.set_data)
                    container.append(widget)

                case 'time':
                    widget = NodeTimePicker(row_data.get_data,
                                            row_data.set_data)
                    container.append(widget)

                case 'datetime':
                    widget = NodeDateTimePicker(row_data.get_data,
                                                row_data.set_data)
                    container.append(widget)

                case 'dropdown':
                    widget = NodeDropdown(row_data.get_data,
                                          row_data.set_data,
                                          options)
                    container.append(widget)

                case 'entry':
                    widget = NodeEntry(None,
                                       row_data.get_data,
                                       row_data.set_data)
                    container.append(widget)

                case 'radio':
                    widget = NodeDropdown(row_data.get_data,
                                          row_data.set_data,
                                          options)
                    container.append(widget)

            return row_data

        def setup_uinterface() -> None:
            """"""
            dtype = next(iter(tschema.values()))

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
                    {c: c for c in list(tschema.keys())},
                ),
                (
                    'operator',
                    get_operators(dtype),
                ),
            ]

            def hide_first_grouper() -> None:
                """"""
                if len(self.clauses) == 0:
                    return
                box = self.get_first_child()
                subbox = box.get_first_child()
                grouper = subbox.get_first_child()
                grouper.set_visible(False)

            def add_list_item(clause: list) -> None:
                """"""
                row = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL)
                row.add_css_class('linked')
                self.append(row)

                box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL,
                              hexpand     = True)
                box.add_css_class('linked')
                row.append(box)

                # For the grouper radio buttons
                subbox = Gtk.Box(hexpand = True)
                box.append(subbox)

                # Populate the new row with blank widgets
                if not clause:
                    for index, content in enumerate(contents):
                        # Fill the data holder with default valuess
                        _, options = content
                        value = next(iter(options.keys()))
                        clause.append(value)

                        create_child_widget(clause, index, content, subbox)

                        # For the column and operator dropdown buttons
                        if index == 0:
                            subbox = Gtk.Box(orientation = Gtk.Orientation.VERTICAL,
                                             hexpand     = True)
                            subbox.add_css_class('linked')
                            box.append(subbox)

                    self.clauses.append(clause)

                # Create widgets based on the given clause data
                else:
                    _dtype = tschema.get(clause[1], dtype)
                    _contents = contents[:-1]
                    _contents.append(('operator', get_operators(_dtype)))

                    for index, content in enumerate(_contents):
                        create_child_widget(clause, index, content, subbox)

                        # For the column and operator dropdown buttons
                        if index == 0:
                            subbox = Gtk.Box(orientation = Gtk.Orientation.VERTICAL,
                                             hexpand     = True)
                            subbox.add_css_class('linked')
                            box.append(subbox)

                    # Other widgets will be generated automatically after
                    # creating the operator dropdown button

                def on_delete_button_clicked(button: Gtk.Button) -> None:
                    """"""
                    self.remove(row)
                    index = next(i for i, x in enumerate(self.clauses) if x is clause)
                    del self.clauses[index]
                    hide_first_grouper()
                    set_data(deepcopy(self.clauses))

                delete_button = Gtk.Button(icon_name = 'user-trash-symbolic')
                delete_button.add_css_class('error')
                delete_button.connect('clicked', on_delete_button_clicked)
                row.append(delete_button)

            self.is_restoring = True

            for clause in self.clauses:
                add_list_item(clause)

            if self.clauses:
                hide_first_grouper()

            self.is_restoring = False

            content = Adw.ButtonContent(label     = f'{_('Add')} {_('Clause')}',
                                        icon_name = 'list-add-symbolic')
            add_button = Gtk.Button(child = content)
            self.append(add_button)

            def on_add_button_clicked(button: Gtk.Button) -> None:
                """"""
                add_list_item([])
                self.remove(add_button)
                self.append(add_button)
                hide_first_grouper()
                set_data(deepcopy(self.clauses))

            add_button.connect('clicked', on_add_button_clicked)

        setup_uinterface()