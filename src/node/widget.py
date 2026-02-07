# widget.py
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

from copy import copy
from copy import deepcopy
from gi.repository import Adw
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Pango
from typing import Any

from ..core.utils import isiterable

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
            selection = copy(get_data())
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

        icon = Gtk.Image(icon_name = 'pan-down-symbolic')
        subbox.append(icon)

        super().__init__(child = box)

        def on_clicked(button: Gtk.Button,
                       label:  Gtk.Label,
                       ) ->    None:
            """"""
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

                def do_remove() -> None:
                    """"""
                    popover.unparent()

                GLib.timeout_add(1000, do_remove)

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



class NodeDropdown(Gtk.DropDown):

    __gtype_name__ = 'NodeDropdown'

    def __init__(self,
                 get_data: callable,
                 set_data: callable,
                 options:  dict,
                 ) ->      None:
        """"""
        super().__init__()

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



class NodeEntry(Gtk.Entry):

    __gtype_name__ = 'NodeEntry'

    def __init__(self,
                 get_data:    callable,
                 set_data:    callable,
                 placeholder: str = _('Value'),
                 ) ->         None:
        """"""
        default = get_data()

        super().__init__(text             = default,
                         placeholder_text = placeholder,
                         tooltip_text     = placeholder)

        def on_activated(entry: Gtk.Entry) -> None:
            """"""
            set_data(entry.get_text())
            self.grab_focus()

        self.connect('activate', on_activated)

        if isinstance(default, (int, float)):
            self.set_input_purpose(Gtk.InputPurpose.NUMBER)

            def on_changed(entry: Adw.EntryRow) -> None:
                """"""
                text = entry.get_text()
                try:
                    if isinstance(default, int):
                        int(text)
                    if isinstance(default, float):
                        float(text)
                except:
                    entry.add_css_class('warning')
                else:
                    entry.remove_css_class('warning')

            self.connect('changed', on_changed)

    def set_data(self,
                 value: str,
                 ) ->   None:
        """"""
        self.set_text(str(value))



class NodeFileChooser(Gtk.Button):

    __gtype_name__ = 'NodeFileChooser'

    def __init__(self,
                 get_data:   callable,
                 on_clicked: callable,
                 ) ->        None:
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

        self._data = deepcopy(get_data())

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
                            value = next(iter(options.values()))
                            idata.append(value)
                        case 'entry':
                            idata.append('')
                        case _:
                            idata.append(None)

                self._data.append(idata)

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
                        widget = NodeEntry(item_data.get_data,
                                           item_data.set_data)
                        subbox.append(widget)

            def on_delete_button_clicked(button: Gtk.Button) -> None:
                """"""
                self.remove(box)
                dat_index = self._data.index(idata)
                del self._data[dat_index]
                set_data(deepcopy(self._data))

            delete_button = Gtk.Button(icon_name = 'user-trash-symbolic')
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

        label = Gtk.Label(label  = get_data(),
                          xalign = 1.0)
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
