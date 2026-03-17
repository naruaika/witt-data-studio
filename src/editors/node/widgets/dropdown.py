# dropdown.py
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

from gi.repository import GLib
from gi.repository import Gtk

class NodeDropDown(Gtk.DropDown):

    __gtype_name__ = 'NodeDropDown'

    def __init__(self,
                 get_data: callable,
                 set_data: callable,
                 options:  dict,
                 ) ->      None:
        """"""
        super().__init__(hexpand = True)

        self._get_data = get_data
        self._set_data = set_data
        self._options  = options

        model = Gtk.StringList()
        for option in options.values():
            model.append(option)
        self.set_model(model)

        list_factory = Gtk.SignalListItemFactory()
        list_factory.connect('setup', self._setup_list_factory)
        list_factory.connect('bind', self._bind_list_factory)
        self.set_list_factory(list_factory)

        factory_bytes = GLib.Bytes.new(self._get_factory_bytes())
        factory = Gtk.BuilderListItemFactory.new_from_bytes(None, factory_bytes)
        self.set_factory(factory)

        if options:
            selected = next((i for i, k in enumerate(options) if k == get_data()), 0)
            self.set_selected(selected)

    def _setup_list_factory(self,
                            list_item_factory: Gtk.SignalListItemFactory,
                            list_item:         Gtk.ListItem,
                            ) ->               None:
        """"""
        box = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL,
                      hexpand     = True)
        list_item.set_child(box)

        label = Gtk.Label()
        box.append(label)

        image = Gtk.Image(icon_name = 'object-select-symbolic',
                          opacity   = 0.0)
        box.append(image)

        list_item.label = label
        list_item.image = image
        list_item.handler = None

    def _bind_list_factory(self,
                           list_item_factory: Gtk.SignalListItemFactory,
                           list_item:         Gtk.ListItem,
                           ) ->               None:
        """"""
        item_data = list_item.get_item()
        label = item_data.get_string()

        list_item.label.set_label(label)

        def do_select() -> bool:
            """"""
            is_selected = list_item.get_selected()
            list_item.image.set_opacity(is_selected)
            if is_selected:
                self.set_tooltip_text(label)
            return is_selected

        if list_item.handler:
            list_item.disconnect(list_item.handler)

        def on_selected(*args) -> None:
            """"""
            if do_select():
                value = next(k for k, v in self._options.items() if v == label)
                self._set_data(value)

        list_item.handler = self.connect('notify::selected-item', on_selected)

        do_select()

    def _get_factory_bytes(self) -> bytes:
        """"""
        return bytes(
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
            """,
            'utf-8',
        )