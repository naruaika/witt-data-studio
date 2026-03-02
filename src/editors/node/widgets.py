# widget.py
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
from gi.repository import Adw
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Pango
from typing import Any

from ...core.utils import isiterable

class NodeCheckButton(Gtk.CheckButton):

    __gtype_name__ = 'NodeCheckButton'

    def __init__(self,
                 title:    str,
                 get_data: callable,
                 set_data: callable,
                 ) ->      None:
        """"""
        label = Gtk.Label(label        = title,
                          xalign       = 0.0,
                          hexpand      = True,
                          ellipsize    = Pango.EllipsizeMode.END,
                          tooltip_text = title)

        super().__init__(active = get_data(),
                         child  = label)

        def on_toggled(button: Gtk.CheckButton) -> None:
            """"""
            active = button.get_active()
            set_data(active)

        self.handler_id = self.connect('toggled', on_toggled)

    def set_data(self,
                 value: bool,
                 ) ->   None:
        """"""
        self.handler_block(self.handler_id)
        self.set_active(value)
        self.handler_unblock(self.handler_id)



class NodeCheckGroup(Gtk.Box):

    __gtype_name__ = 'NodeCheckGroup'

    def __init__(self,
                 get_data: callable,
                 set_data: callable,
                 options:  list[str],
                 ) ->      None:
        """"""
        super().__init__(orientation = Gtk.Orientation.VERTICAL)

        self.add_css_class('linked')

        def on_toggled(button: Gtk.CheckButton,
                       value:  str,
                       ) ->    None:
            """"""
            selection = deepcopy(get_data())
            if button.get_active():
                selection.append(value)
            else:
                selection.remove(value)
            set_data(selection)

        for option in options:
            label = Gtk.Label(halign       = Gtk.Align.START,
                              valign       = Gtk.Align.CENTER,
                              hexpand      = True,
                              ellipsize    = Pango.EllipsizeMode.END,
                              label        = option,
                              tooltip_text = option)
            active = option in get_data()
            check = Gtk.CheckButton(child  = label,
                                    active = active)
            check.connect('toggled', on_toggled, option)
            self.append(check)



class NodeComboButton(Gtk.Button):

    __gtype_name__ = 'NodeComboButton'

    def __init__(self,
                 title:    str,
                 get_data: callable,
                 set_data: callable,
                 options:  dict,
                 ) ->      None:
        """"""
        self.icon = Gtk.Image(icon_name = 'pan-down-symbolic')

        self.set_options(options)

        box = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL,
                      spacing     = 6)

        label = Gtk.Label(label        = title,
                          xalign       = 0.0,
                          hexpand      = True,
                          ellipsize    = Pango.EllipsizeMode.END,
                          tooltip_text = title)
        box.append(label)

        subbox = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL,
                         spacing     = 2)
        box.append(subbox)

        label = next((v for k, v in self.options.items() if k == get_data()), None)
        label = Gtk.Label(label        = label,
                          xalign       = 1.0,
                          ellipsize    = Pango.EllipsizeMode.END,
                          tooltip_text = label)

        subbox.append(label)
        subbox.append(self.icon)

        super().__init__(child = box)

        def on_clicked(button: Gtk.Button,
                       label:  Gtk.Label,
                       ) ->    None:
            """"""
            if len(self.options) < 2:
                return

            def setup_factory(list_item_factory: Gtk.SignalListItemFactory,
                              list_item:         Gtk.ListItem,
                              ) ->               None:
                """"""
                list_item.set_focusable(False)

                container = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL,
                                    hexpand     = True,
                                    spacing     = 6)
                list_item.set_child(container)

                label = Gtk.Label(halign    = Gtk.Align.START,
                                  valign    = Gtk.Align.CENTER,
                                  ellipsize = Pango.EllipsizeMode.END)
                container.append(label)

                image = Gtk.Image(icon_name = 'object-select-symbolic',
                                  opacity   = 0.0)
                container.append(image)

                list_item.image = image
                list_item.label = label

            def bind_factory(list_item_factory: Gtk.SignalListItemFactory,
                             list_item:         Gtk.ListItem,
                             list_head:         Gtk.Label,
                             ) ->               None:
                """"""
                item_data = list_item.get_item()
                item_data = item_data.get_string()
                container = list_item.get_child()

                list_item.label.set_label(item_data)
                container.set_tooltip_text(item_data)

                if list_head.get_label() == item_data:
                    list_item.image.set_opacity(1.0)
                else:
                    list_item.image.set_opacity(0.0)

            model = Gtk.StringList()
            for value in self.options.values():
                model.append(value)
            selection = Gtk.NoSelection(model = model)

            factory = Gtk.SignalListItemFactory()
            factory.connect('setup', setup_factory)
            factory.connect('bind', bind_factory, label)
            list_view = Gtk.ListView(model                 = selection,
                                     factory               = factory,
                                     single_click_activate = True)
            list_view.add_css_class('navigation-sidebar')

            box = Gtk.ScrolledWindow(child                    = list_view,
                                     propagate_natural_width  = True,
                                     propagate_natural_height = True)

            popover = Gtk.Popover(child = box)
            popover.set_parent(button)

            rect = Gdk.Rectangle()
            rect.x = button.get_width() - 8
            rect.y = button.get_height() / 2 + 4
            rect.width = 1
            rect.height = 1
            popover.set_pointing_to(rect)
            popover.popup()

            button.add_css_class('has-open-popup')

            def on_activated(list_view: Gtk.ListView,
                             position:  int,
                             ) ->       None:
                """"""
                key = list(self.options.keys())[position]
                value = list(self.options.values())[position]
                label.set_label(value)
                label.set_tooltip_text(value)
                popover.popdown()
                set_data(key)

            list_view.connect('activate', on_activated)

            def on_closed(popover: Gtk.Popover) -> None:
                """"""
                button.remove_css_class('has-open-popup')
                GLib.timeout_add(1000, popover.unparent)

            popover.connect('closed', on_closed)

        self.connect('clicked', on_clicked, label)

    def set_data(self,
                 value: str,
                 ) ->   None:
        """"""
        box = self.get_child()
        subbox = box.get_last_child()
        label = subbox.get_first_child()
        label.set_label(value)
        label.set_tooltip_text(value)

    def set_options(self,
                    options: dict,
                    ) ->     None:
        """"""
        self.options = options
        if isinstance(options, list):
            self.options = {o: o for o in options}

        if len(options) == 1:
            self.icon.set_visible(False)
        else:
            self.icon.set_visible(True)

        if len(options) == 0:
            self.icon.set_from_icon_name('exclamation-mark-symbolic')
        else:
            self.icon.set_from_icon_name('pan-down-symbolic')



class NodeDatabaseReader(Gtk.Button):

    __gtype_name__ = 'NodeDatabaseReader'

    def __init__(self,
                 get_data: callable,
                 set_data: callable,
                 ) ->      None:
        """"""
        label = Gtk.Label(label            = get_data()['query'],
                          xalign           = 0.0,
                          ellipsize        = Pango.EllipsizeMode.END,
                          single_line_mode = True)
        label.add_css_class('monospace')

        super().__init__(child = label)

        def on_clicked(button: Gtk.Button) -> None:
            """"""
            window = self.get_root()
            application = window.get_application()

            data = get_data()
            query = data['query']
            config = data['config']

            from ...ui.database_import.widget import DatabaseImportWindow
            importer = DatabaseImportWindow(query         = query,
                                            config        = config,
                                            callback      = set_data,
                                            transient_for = window,
                                            application   = application)
            importer.present()

        self.connect('clicked', on_clicked)

    def set_data(self,
                 value: str,
                 ) ->   None:
        """"""
        label = self.get_child()
        label.set_label(str(value))



class NodeDropdown(Gtk.DropDown):

    __gtype_name__ = 'NodeDropdown'

    def __init__(self,
                 get_data: callable,
                 set_data: callable,
                 options:  dict,
                 ) ->      None:
        """"""
        super().__init__(hexpand = True)

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
                    self.set_tooltip_text(label)
                return is_selected

            def on_selected(*args) -> None:
                """"""
                if do_select():
                    value = next((key for key, val in options.items() if val == label), None)
                    set_data(value)

            list_item.label.set_label(label)

            if list_item.bind_item:
                list_item.disconnect(list_item.bind_item)

            list_item.bind_item = self.connect('notify::selected', on_selected)

            do_select()

        model = Gtk.StringList()
        for option in options.values():
            model.append(option)
        self.set_model(model)

        list_factory = Gtk.SignalListItemFactory()
        list_factory.connect('setup', setup_factory)
        list_factory.connect('bind', bind_factory)
        self.set_list_factory(list_factory)

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
        self.set_factory(factory)

        selected = next((i for i, key in enumerate(options) if key == get_data()), 0)
        self.set_selected(selected)



class NodeEntry(Gtk.Button):

    __gtype_name__ = 'NodeEntry'

    def __init__(self,
                 title:    str,
                 get_data: callable,
                 set_data: callable,
                 ) ->      None:
        """"""
        self.is_empty = get_data() == ''

        from ...core.evaluators.arithmetic import Evaluator
        evaluator = Evaluator()

        box = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL,
                      spacing     = 6)

        if title:
            label = Gtk.Label(label        = title,
                              xalign       = 0.0,
                              hexpand      = True,
                              ellipsize    = Pango.EllipsizeMode.END,
                              tooltip_text = title)
            box.append(label)

        text = get_data() if not self.is_empty else f'[{_('Empty')}]'

        label = Gtk.Label(label     = text,
                          xalign    = 1.0,
                          ellipsize = Pango.EllipsizeMode.END)
        box.append(label)

        super().__init__(child = box)

        def on_clicked(button: Gtk.Button,
                       label:  Gtk.Label,
                       ) ->    None:
            """"""
            value = label.get_label() if not self.is_empty else ''
            entry = Gtk.Entry(text             = value,
                              placeholder_text = title)

            if isinstance(get_data(), (int, float)):
                entry.set_input_purpose(Gtk.InputPurpose.NUMBER)

            entry.add_css_class('node-widget')
            if button.has_css_class('before-socket'):
                entry.add_css_class('before-socket')
            if button.has_css_class('after-socket'):
                entry.add_css_class('after-socket')

            container = button.get_parent()
            container.insert_child_after(entry, button)
            button.unparent()

            args = (container, button, label, entry)

            def do_apply(args: list[Any]) -> None:
                """"""
                container, button, label, entry = args
                text = entry.get_text()

                if isinstance(get_data(), (int, float)):
                    try:
                        text = evaluator.evaluate(text)
                        if isinstance(get_data(), int):
                            text = int(text)
                        if isinstance(get_data(), float):
                            text = float(text)
                    except:
                        return

                text = str(text)
                self.is_empty = text == ''
                text = text if not self.is_empty else f'[{_('Empty')}]'

                label.set_label(text)
                container.insert_child_after(button, entry)
                entry.unparent()
                set_data(text)

            def on_activated(entry: Gtk.Entry,
                             args:  list[Any],
                             ) ->   None:
                """"""
                do_apply(args)

            entry.connect('activate', on_activated, args)

            def on_key_pressed(event:   Gtk.EventControllerKey,
                               keyval:  int,
                               keycode: int,
                               state:   Gdk.ModifierType,
                               args:    list[Any],
                               ) ->     bool:
                """"""
                if keyval == Gdk.KEY_Escape:
                    do_apply(args)
                    return Gdk.EVENT_STOP
                return Gdk.EVENT_PROPAGATE

            controller = Gtk.EventControllerKey()
            controller.connect('key-pressed', on_key_pressed, args)
            entry.add_controller(controller)

            def on_changed(entry: Gtk.Entry) -> None:
                """"""
                text = entry.get_text()
                try:
                    text = evaluator.evaluate(text)
                    if isinstance(get_data(), int):
                        int(text)
                    if isinstance(get_data(), float):
                        float(text)
                except:
                    entry.add_css_class('warning')
                else:
                    entry.remove_css_class('warning')

            if isinstance(get_data(), (int, float)):
                entry.connect('changed', on_changed)

            def do_focus() -> bool:
                """"""
                entry.grab_focus()
                return Gdk.EVENT_PROPAGATE

            GLib.timeout_add(50, do_focus)

        self.connect('clicked', on_clicked, label)

    def get_data(self) -> str:
        """"""
        box = self.get_child()
        label = box.get_last_child()
        return label.get_label()

    def set_data(self,
                 value: str,
                 ) ->   None:
        """"""
        value = str(value)
        self.is_empty = value == ''
        value = value if not self.is_empty else f'[{_('Empty')}]'

        box = self.get_child()
        label = box.get_last_child()
        label.set_label(value)



class NodeFileReader(Gtk.Button):

    __gtype_name__ = 'NodeFileReader'

    def __init__(self,
                 get_data: callable,
                 set_data: callable,
                 ) ->      None:
        """"""
        box = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL,
                      spacing     = 6)

        label = Gtk.Label(label     = get_data() or _('Choose File...'),
                          xalign    = 0.0,
                          hexpand   = True,
                          ellipsize = Pango.EllipsizeMode.END)
        box.append(label)

        icon = Gtk.Image(icon_name = 'folder-open-symbolic')
        box.append(icon)

        super().__init__(child = box)

        def on_clicked(button: Gtk.Button) -> None:
            """"""
            window = self.get_root()

            from ...ui.file_dialog import FileDialog
            FileDialog.open(window, set_data)

        self.connect('clicked', on_clicked)

    def set_data(self,
                 value: str,
                 ) ->   None:
        """"""
        box = self.get_child()
        label = box.get_first_child()
        if value:
            label.set_label(value)
            label.set_ellipsize(Pango.EllipsizeMode.START)
        else:
            label.set_label(_('Choose File...'))
            label.set_ellipsize(Pango.EllipsizeMode.END)
        self.set_tooltip_text(value)



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



class NodeFormulaEditor(Gtk.Button):

    __gtype_name__ = 'NodeFormulaEditor'

    def __init__(self,
                 get_data: callable,
                 set_data: callable,
                 ) ->      None:
        """"""
        label = Gtk.Label(label            = get_data(),
                          xalign           = 0.0,
                          ellipsize        = Pango.EllipsizeMode.END,
                          single_line_mode = True)
        label.add_css_class('monospace')

        super().__init__(child = label)

        def do_apply(formula: str) -> None:
            """"""
            set_data(formula)
            self.set_data(formula)

        def on_clicked(button: Gtk.Button) -> None:
            """"""
            window = self.get_root()
            application = window.get_application()

            from ...ui.formula_editor.widget import FormulaEditorWindow
            editor = FormulaEditorWindow(subtitle      = None,
                                         callback      = do_apply,
                                         transient_for = window,
                                         application   = application,
                                         formula       = get_data())
            editor.present()

        self.connect('clicked', on_clicked)

    def set_data(self,
                 value: str,
                 ) ->   None:
        """"""
        label = self.get_child()
        label.set_label(str(value))



class NodeLabel(Gtk.Label):

    __gtype_name__ = 'NodeLabel'

    def __init__(self,
                 label:    str,
                 can_link: bool = False,
                 ) ->      None:
        """"""
        super().__init__(label     = label,
                         xalign    = 1.0,
                         ellipsize = Pango.EllipsizeMode.END)

        self.add_css_class('node-label')

        if can_link:
            self.set_xalign(0.0)
            self.add_css_class('after-socket')
            self.add_css_class('node-widget')



class NodeListEntry(Gtk.Box):

    __gtype_name__ = 'NodeListEntry'

    def __init__(self,
                 title:    str,
                 get_data: callable,
                 set_data: callable,
                 contents: list,
                 ) ->      None:
        """"""
        super().__init__(orientation = Gtk.Orientation.VERTICAL,
                         spacing     = 6)

        self._data = deepcopy(get_data())

        _contents = [('entry')] + contents

        class ItemData():

            def __init__(self,
                         mdata: list,
                         idata: list,
                         index: int,
                         ) ->   None:
                """"""
                self.mdata = mdata
                self.idata = idata
                self.index = index

            def get_data(self) -> str:
                """"""
                return self.idata[self.index]

            def set_data(self,
                         value: str,
                         ) ->   None:
                """"""
                self.idata[self.index] = value
                set_data(deepcopy(self.mdata))

        def add_list_item(idata: list) -> None:
            """"""
            box = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL)
            box.add_css_class('linked')
            self.append(box)

            subbox = Gtk.Box(orientation = Gtk.Orientation.VERTICAL,
                             homogeneous = True,
                             hexpand     = True)
            subbox.add_css_class('linked')
            box.append(subbox)

            if not idata:
                for index, content in enumerate(_contents):
                    if isiterable(content):
                        dtype, options = content
                        if isinstance(options, list):
                            options = {o: o for o in options}
                        _contents[index] = (dtype, options)
                    else:
                        dtype = content

                    match dtype:
                        case 'dropdown':
                            value = next(iter(options.keys()))
                            idata.append(value)
                        case 'entry':
                            idata.append('')
                        case _:
                            idata.append(None)

                self._data.append(idata)

            for index, content in enumerate(_contents):
                if isiterable(content):
                    dtype, options = content
                else:
                    dtype = content

                item_data = ItemData(self._data, idata, index)

                match dtype:
                    case 'dropdown':
                        widget = NodeDropdown(item_data.get_data,
                                              item_data.set_data,
                                              options)
                        subbox.append(widget)

                    case 'entry':
                        widget = NodeEntry(None,
                                           item_data.get_data,
                                           item_data.set_data)
                        subbox.append(widget)

            def on_delete_button_clicked(button: Gtk.Button) -> None:
                """"""
                self.remove(box)
                index = next(i for i, x in enumerate(self._data) if x is idata)
                del self._data[index]
                set_data(deepcopy(self._data))

            delete_button = Gtk.Button(icon_name = 'user-trash-symbolic')
            delete_button.add_css_class('error')
            delete_button.connect('clicked', on_delete_button_clicked)
            box.append(delete_button)

        for __data in self._data:
            add_list_item(__data)

        content = Adw.ButtonContent(label     = f'{_('Add')} {title}',
                                    icon_name = 'list-add-symbolic')
        add_button = Gtk.Button(child = content)
        self.append(add_button)

        def on_add_button_clicked(button: Gtk.Button) -> None:
            """"""
            add_list_item([])
            set_data(deepcopy(self._data))
            self.remove(add_button)
            self.append(add_button)

        add_button.connect('clicked', on_add_button_clicked)



class NodeListItem(Gtk.Box):

    __gtype_name__ = 'NodeListItem'

    def __init__(self,
                 title:    str,
                 get_data: callable,
                 set_data: callable,
                 contents: list,
                 ) ->      None:
        """"""
        super().__init__(orientation = Gtk.Orientation.VERTICAL,
                         spacing     = 6)

        self._data: list = deepcopy(get_data())

        class ItemData():

            def __init__(self,
                         mdata: list,
                         idata: list,
                         index: int,
                         ) ->   None:
                """"""
                self.mdata = mdata
                self.idata = idata
                self.index = index

            def get_data(self) -> str:
                """"""
                return self.idata[self.index]

            def set_data(self,
                         value: str,
                         ) ->   None:
                """"""
                self.idata[self.index] = value
                set_data(deepcopy(self.mdata))

        def add_list_item(idata: list) -> None:
            """"""
            box = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL)
            box.add_css_class('linked')
            self.append(box)

            subbox = Gtk.Box(orientation = Gtk.Orientation.VERTICAL,
                             hexpand     = True)
            subbox.add_css_class('linked')
            box.append(subbox)

            # Fill the data holder with default values
            if not idata:
                for index, content in enumerate(contents):
                    if isiterable(content):
                        dtype, options = content
                        if isinstance(options, list):
                            options = {o: o for o in options}
                        contents[index] = (dtype, options)
                    else:
                        dtype = content

                    match dtype:
                        case 'dropdown':
                            value = next(iter(options.keys()))
                            idata.append(value)
                        case 'entry':
                            idata.append('')
                        case _:
                            idata.append(None)

                self._data.append(idata)

            # Populate the new row with blank widgets
            for index, content in enumerate(contents):
                if isiterable(content):
                    dtype, options = content
                else:
                    dtype = content

                item_data = ItemData(self._data, idata, index)

                match dtype:
                    case 'dropdown':
                        widget = NodeDropdown(item_data.get_data,
                                              item_data.set_data,
                                              options)
                        subbox.append(widget)

                    case 'entry':
                        widget = NodeEntry(None,
                                           item_data.get_data,
                                           item_data.set_data)
                        subbox.append(widget)

            def on_delete_button_clicked(button: Gtk.Button) -> None:
                """"""
                self.remove(box)
                index = next(i for i, x in enumerate(self._data) if x is idata)
                del self._data[index]
                set_data(deepcopy(self._data))

            delete_button = Gtk.Button(icon_name = 'user-trash-symbolic')
            delete_button.add_css_class('error')
            delete_button.connect('clicked', on_delete_button_clicked)
            box.append(delete_button)

        for idata in self._data:
            add_list_item(idata)

        content = Adw.ButtonContent(label     = f'{_('Add')} {title}',
                                    icon_name = 'list-add-symbolic')
        add_button = Gtk.Button(child = content)
        self.append(add_button)

        def on_add_button_clicked(button: Gtk.Button) -> None:
            """"""
            add_list_item([])
            self.remove(add_button)
            self.append(add_button)
            set_data(deepcopy(self._data))

        add_button.connect('clicked', on_add_button_clicked)



class NodeRadio(Gtk.Box):

    __gtype_name__ = 'NodeRadio'

    def __init__(self,
                 get_data: callable,
                 set_data: callable,
                 options:  dict,
                 ) ->      None:
        """"""
        super().__init__(orientation = Gtk.Orientation.VERTICAL,
                         homogeneous = True,
                         hexpand     = True)

        self.add_css_class('linked')

        self.handler_ids = []

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
            check_button.connect('toggled', on_toggled)
            self.append(check_button)

            if primary_button:
                check_button.set_group(primary_button)
            else:
                primary_button = check_button

            if key == get_data():
                check_button.set_active(True)



class NodeSpinButton(Gtk.Button):

    __gtype_name__ = 'NodeSpinButton'

    def __init__(self,
                 title:    str,
                 get_data: callable,
                 set_data: callable,
                 lower:    float = None,
                 upper:    float = None,
                 digits:   int   = 3,
                 ) ->      None:
        """"""
        box = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL,
                      spacing     = 6)

        label = Gtk.Label(label        = title,
                          xalign       = 0.0,
                          hexpand      = True,
                          ellipsize    = Pango.EllipsizeMode.END,
                          tooltip_text = title)
        box.append(label)

        label = Gtk.Label(label     = get_data(),
                          xalign    = 1.0,
                          ellipsize = Pango.EllipsizeMode.END)
        box.append(label)

        super().__init__(child = box)

        def on_clicked(button: Gtk.Button,
                       label:  Gtk.Label,
                       lower:  float,
                       upper:  float,
                       ) ->    None:
            """"""
            value = label.get_label()
            value = int(value) if digits == 0 else float(value)
            lower = -GLib.MAXDOUBLE if lower is None else lower
            upper = +GLib.MAXDOUBLE if upper is None else upper

            adjustment = Gtk.Adjustment(value          = value,
                                        lower          = lower,
                                        upper          = upper,
                                        step_increment = 1,
                                        page_increment = 10,
                                        page_size      = 10)
            spin = Gtk.SpinButton(numeric    = True,
                                  adjustment = adjustment,
                                  hexpand    = True,
                                  digits     = digits)

            spin.add_css_class('node-widget')
            if button.has_css_class('before-socket'):
                spin.add_css_class('before-socket')
            if button.has_css_class('after-socket'):
                spin.add_css_class('after-socket')

            container = button.get_parent()
            container.insert_child_after(spin, button)
            button.unparent()

            args = (container, button, label, spin)
            text = spin.get_first_child()

            def do_apply(args: list[Any]) -> None:
                """"""
                container, button, label, spin = args
                value = spin.get_value()
                value = int(value) if digits == 0 else float(value)
                label.set_label(str(value))
                container.insert_child_after(button, spin)
                spin.unparent()
                set_data(value)

            def on_activated(spin: Gtk.SpinButton,
                             args: list[Any],
                             ) ->  None:
                """"""
                do_apply(args)

            text.connect('activate', on_activated, args)

            def on_key_pressed(event:   Gtk.EventControllerKey,
                               keyval:  int,
                               keycode: int,
                               state:   Gdk.ModifierType,
                               args:    list[Any],
                               ) ->     bool:
                """"""
                if keyval == Gdk.KEY_Escape:
                    do_apply(args)
                    return Gdk.EVENT_STOP
                return Gdk.EVENT_PROPAGATE

            controller = Gtk.EventControllerKey()
            controller.connect('key-pressed', on_key_pressed, args)
            text.add_controller(controller)

            def do_focus() -> bool:
                """"""
                spin.grab_focus()
                return Gdk.EVENT_PROPAGATE

            GLib.timeout_add(50, do_focus)

        args = (label, lower, upper)
        self.connect('clicked', on_clicked, *args)

    def set_data(self,
                 value: float,
                 ) ->   None:
        """"""
        box = self.get_child()
        label = box.get_last_child()
        label.set_label(str(value))



class NodeDatePicker(Gtk.Button):

    __gtype_name__ = 'NodeDatePicker'

    def __init__(self,
                 get_data: callable,
                 set_data: callable,
                 ) ->      None:
        """"""
        import datetime

        entry = Gtk.Entry()
        entry.add_css_class('node-widget')

        from ...ui.date_picker import DatePicker
        picker = DatePicker(halign            = Gtk.Align.CENTER,
                            show_week_numbers = True,
                            margin_top        = 5,
                            margin_bottom     = 5,
                            margin_start      = 5,
                            margin_end        = 5)
        popover = Gtk.Popover(child = picker)

        def on_icon_pressed(entry:    Gtk.Entry,
                            icon_pos: Gtk.EntryIconPosition,
                            ) ->      None:
            """"""
            if icon_pos == Gtk.EntryIconPosition.SECONDARY:
                rect = entry.get_icon_area(icon_pos)
                popover.set_pointing_to(rect)
                popover.popup()

        entry.set_icon_from_icon_name(icon_pos  = Gtk.EntryIconPosition.SECONDARY,
                                      icon_name = 'vcal-symbolic')
        entry.connect('icon-press', on_icon_pressed)

        def _get_data() -> str:
            """"""
            return get_data().strftime('%Y-%m-%d')

        def _set_data(value:  str,
                      submit: bool,
                      ) ->    None:
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
                if submit:
                    set_data(value)

        popover.set_parent(entry)

        is_empty = get_data() == ''

        box = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL,
                      spacing     = 6)

        label = Gtk.Label(label     = get_data() or f'[{_('Empty')}]',
                          xalign    = 1.0,
                          ellipsize = Pango.EllipsizeMode.END)
        box.append(label)

        if isinstance(get_data(), datetime.date):
            picker.set_year(get_data().year)
            picker.set_month(get_data().month)
            picker.set_day(get_data().day)

        def on_calendar_updated(widget: DatePicker) -> None:
            """"""
            value: datetime.date = get_data()
            value = value.replace(widget.get_year(),
                                  widget.get_month() + 1,
                                  widget.get_day())
            value = value.strftime('%Y-%m-%d')

            if entry.get_text() != value:
                entry.remove_css_class('warning')
                entry.set_text(value)

        picker.connect('day-selected', on_calendar_updated)
        picker.connect('next-month', on_calendar_updated)
        picker.connect('next-year', on_calendar_updated)
        picker.connect('prev-month', on_calendar_updated)
        picker.connect('prev-year', on_calendar_updated)

        super().__init__(child = box)

        if self.has_css_class('before-socket'):
            entry.add_css_class('before-socket')
        if self.has_css_class('after-socket'):
            entry.add_css_class('after-socket')

        def on_clicked(button: Gtk.Button,
                       label:  Gtk.Label,
                       ) ->    None:
            """"""
            value = label.get_label() if not is_empty else ''
            entry.set_text(value)

            container = button.get_parent()
            container.insert_child_after(entry, button)
            button.unparent()

            args = (container, button, label, entry)

            def do_apply(args: list[Any]) -> None:
                """"""
                nonlocal is_empty

                container, button, label, entry = args
                text = entry.get_text()

                text = str(text)
                is_empty = text == ''

                label.set_label(text or f'[{_('Empty')}]')
                container.insert_child_after(button, entry)
                entry.unparent()
                _set_data(text, True)

            def on_activated(entry: Gtk.Entry,
                             args:  list[Any],
                             ) ->   None:
                """"""
                do_apply(args)

            entry.connect('activate', on_activated, args)

            def on_key_pressed(event:   Gtk.EventControllerKey,
                               keyval:  int,
                               keycode: int,
                               state:   Gdk.ModifierType,
                               args:    list[Any],
                               ) ->     bool:
                """"""
                if keyval == Gdk.KEY_Escape:
                    do_apply(args)
                    return Gdk.EVENT_STOP
                return Gdk.EVENT_PROPAGATE

            controller = Gtk.EventControllerKey()
            controller.connect('key-pressed', on_key_pressed, args)
            entry.add_controller(controller)

            def on_changed(entry: Gtk.Entry) -> None:
                """"""
                text = entry.get_text()
                _set_data(str(text), False)

            entry.connect('changed', on_changed)

            def do_focus() -> bool:
                """"""
                entry.grab_focus()
                return Gdk.EVENT_PROPAGATE

            GLib.timeout_add(50, do_focus)

        self.connect('clicked', on_clicked, label)

    def set_data(self,
                 value: str,
                 ) ->   None:
        """"""
        box = self.get_child()
        label = box.get_last_child()
        label.set_label(str(value))



class NodeTimePicker(Gtk.Button):

    __gtype_name__ = 'NodeTimePicker'

    def __init__(self,
                 get_data: callable,
                 set_data: callable,
                 ) ->      None:
        """"""
        import datetime

        entry = Gtk.Entry()
        entry.add_css_class('node-widget')

        from ...ui.time_picker import TimePicker
        picker = TimePicker(halign = Gtk.Align.CENTER,
                            valign = Gtk.Align.CENTER)
        popover = Gtk.Popover(child = picker)

        def on_icon_pressed(entry:    Gtk.Entry,
                            icon_pos: Gtk.EntryIconPosition,
                            ) ->      None:
            """"""
            if icon_pos == Gtk.EntryIconPosition.SECONDARY:
                picker.set_mode(picker.MODE_HOUR)
                rect = entry.get_icon_area(icon_pos)
                popover.set_pointing_to(rect)
                popover.popup()

        entry.set_icon_from_icon_name(icon_pos  = Gtk.EntryIconPosition.SECONDARY,
                                      icon_name = 'clock-alt-symbolic')
        entry.connect('icon-press', on_icon_pressed)

        def _get_data() -> str:
            """"""
            return get_data().strftime('%H:%M:%S')

        def _set_data(value:  str,
                      submit: bool,
                      ) ->    None:
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
                if submit:
                    set_data(value)

        popover.set_parent(entry)

        is_empty = get_data() == ''

        box = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL,
                      spacing     = 6)

        label = Gtk.Label(label     = get_data() or f'[{_('Empty')}]',
                          xalign    = 1.0,
                          ellipsize = Pango.EllipsizeMode.END)
        box.append(label)

        if isinstance(get_data(), datetime.time):
            picker.set_hour(get_data().hour)
            picker.set_minute(get_data().minute)
            picker.set_second(get_data().second)

        def on_time_updated(widget: TimePicker) -> None:
            """"""
            value: datetime.time = get_data()
            value = value.replace(widget.get_hour(),
                                  widget.get_minute(),
                                  widget.get_second())
            value = value.strftime('%H:%M:%S')

            if entry.get_text() != value:
                entry.remove_css_class('warning')
                entry.set_text(value)

        picker.connect('time-updated', on_time_updated)

        super().__init__(child = box)

        if self.has_css_class('before-socket'):
            entry.add_css_class('before-socket')
        if self.has_css_class('after-socket'):
            entry.add_css_class('after-socket')

        def on_clicked(button: Gtk.Button,
                       label:  Gtk.Label,
                       ) ->    None:
            """"""
            value = label.get_label() if not is_empty else ''
            entry.set_text(value)

            container = button.get_parent()
            container.insert_child_after(entry, button)
            button.unparent()

            args = (container, button, label, entry)

            def do_apply(args: list[Any]) -> None:
                """"""
                nonlocal is_empty

                container, button, label, entry = args
                text = entry.get_text()

                text = str(text)
                is_empty = text == ''

                label.set_label(text or f'[{_('Empty')}]')
                container.insert_child_after(button, entry)
                entry.unparent()
                _set_data(text, True)

            def on_activated(entry: Gtk.Entry,
                             args:  list[Any],
                             ) ->   None:
                """"""
                do_apply(args)

            entry.connect('activate', on_activated, args)

            def on_key_pressed(event:   Gtk.EventControllerKey,
                               keyval:  int,
                               keycode: int,
                               state:   Gdk.ModifierType,
                               args:    list[Any],
                               ) ->     bool:
                """"""
                if keyval == Gdk.KEY_Escape:
                    do_apply(args)
                    return Gdk.EVENT_STOP
                return Gdk.EVENT_PROPAGATE

            controller = Gtk.EventControllerKey()
            controller.connect('key-pressed', on_key_pressed, args)
            entry.add_controller(controller)

            def on_changed(entry: Gtk.Entry) -> None:
                """"""
                text = entry.get_text()
                _set_data(str(text), False)

            entry.connect('changed', on_changed)

            def do_focus() -> bool:
                """"""
                entry.grab_focus()
                return Gdk.EVENT_PROPAGATE

            GLib.timeout_add(50, do_focus)

        self.connect('clicked', on_clicked, label)

    def set_data(self,
                 value: str,
                 ) ->   None:
        """"""
        box = self.get_child()
        label = box.get_last_child()
        label.set_label(str(value))



class NodeDateTimePicker(Gtk.Box):

    __gtype_name__ = 'NodeDateTimePicker'

    def __init__(self,
                 get_data: callable,
                 set_data: callable,
                 ) ->      None:
        """"""
        import datetime

        default: datetime.datetime = get_data()

        super().__init__(orientation = Gtk.Orientation.VERTICAL,
                         hexpand     = True)
        self.add_css_class('linked')

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

        self._date = NodeDatePicker(get_date, set_date)
        self._time = NodeTimePicker(get_time, set_time)

        self.append(self._date)
        self.append(self._time)

    def set_data(self,
                 value: str,
                 ) ->   None:
        """"""
        from datetime import datetime
        value = datetime.fromisoformat(value)
        self._date.set_data(value.date().isoformat())
        self._time.set_data(value.time().isoformat())
