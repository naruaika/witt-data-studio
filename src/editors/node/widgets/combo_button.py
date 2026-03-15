# combo_button.py
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

from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Pango

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

        label = next((v for k, v in self.options.items() if k == get_data()), '')
        label = Gtk.Label(label        = label,
                          xalign       = 1.0,
                          ellipsize    = Pango.EllipsizeMode.END,
                          tooltip_text = label)

        subbox.append(label)
        subbox.append(self.icon)

        super().__init__(child = box)

        self._get_data = get_data
        self._set_data = set_data

        self.connect('clicked', self._on_clicked, label)

    def _on_clicked(self,
                    button: Gtk.Button,
                    label:  Gtk.Label,
                    ) ->    None:
        """"""
        if len(self.options) < 2:
            return

        model = Gtk.StringList()
        for value in self.options.values():
            model.append(value)
        selection = Gtk.NoSelection(model = model)

        factory = Gtk.SignalListItemFactory()
        factory.connect('setup', self._setup_factory)
        factory.connect('bind', self._bind_factory, label)
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

        args = [label, popover]
        list_view.connect('activate', self._on_list_view_activated, *args)

        popover.connect('closed', self._on_popover_closed, button)

    def _setup_factory(self,
                       list_item_factory: Gtk.SignalListItemFactory,
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

    def _bind_factory(self,
                      list_item_factory: Gtk.SignalListItemFactory,
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

    def _on_list_view_activated(self,
                      list_view: Gtk.ListView,
                      position:  int,
                      list_head: Gtk.Label,
                      popover:   Gtk.Popover
                      ) ->       None:
        """"""
        key = list(self.options.keys())[position]
        value = list(self.options.values())[position]

        list_head.set_label(value)
        list_head.set_tooltip_text(value)

        popover.popdown()

        self._set_data(key)

    def _on_popover_closed(self,
                           popover: Gtk.Popover,
                           parent:  Gtk.Button,
                           ) ->     None:
        """"""
        parent.remove_css_class('has-open-popup')
        GLib.timeout_add(250, popover.unparent)

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