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

from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Pango
from sys import float_info
from typing import Any

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

        self.connect('toggled', on_toggled)



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
            selection = get_data()
            if button.get_active():
                selection.append(value)
            else:
                selection.remove(value)
            set_data(selection)

        for column in options:
            label = Gtk.Label(halign       = Gtk.Align.START,
                              valign       = Gtk.Align.CENTER,
                              hexpand      = True,
                              ellipsize    = Pango.EllipsizeMode.END,
                              label        = column,
                              tooltip_text = column)
            active = column in get_data()
            check = Gtk.CheckButton(active = active,
                                    child  = label)
            check.connect('toggled', on_toggled, column)
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

        label = next((key for key, value in options.items()
                      if value == get_data()), None)
        label = Gtk.Label(label  = label,
                          xalign = 1.0)
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
            for value in options:
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
                key = list(options.keys())[position]
                value = list(options.values())[position]
                label.set_label(key)
                popover.popdown()
                set_data(value)

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



class NodeEntry(Gtk.Entry):

    __gtype_name__ = 'NodeEntry'

    def __init__(self,
                 get_data: callable,
                 set_data: callable,
                 ) ->      None:
        """"""
        super().__init__(text = get_data())

        def on_changed(entry: Gtk.Entry) -> None:
            """"""
            set_data(entry.get_text())

        self.connect('changed', on_changed)

        def on_deleted(entry:     Gtk.Entry,
                       start_pos: int,
                       end_pos:   int,
                       ) ->       None:
            """"""
            set_data(entry.get_text())

        self.connect('delete-text', on_deleted)

        def on_inserted(entry:    Gtk.Entry,
                        text:     str,
                        lenght:   int,
                        position: int,
                        ) ->      None:
            """"""
            set_data(text)

        self.connect('insert-text', on_inserted)



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
            lower = lower if lower is not None else float_info.min
            upper = upper if upper is not None else float_info.max
            adjustment = Gtk.Adjustment(value          = value,
                                        lower          = lower,
                                        upper          = upper,
                                        step_increment = 1,
                                        page_increment = 10,
                                        page_size      = 10)
            container = button.get_parent()
            spin = Gtk.SpinButton(numeric    = True,
                                  adjustment = adjustment,
                                  hexpand    = True,
                                  digits     = digits)
            spin.add_css_class('node-widget')
            if button.has_css_class('before-socket'):
                spin.add_css_class('before-socket')
            if button.has_css_class('after-socket'):
                spin.add_css_class('after-socket')
            container.insert_child_after(spin, button)
            button.unparent()
            spin.grab_focus()

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

        args = (label, lower, upper)
        self.connect('clicked', on_clicked, *args)
