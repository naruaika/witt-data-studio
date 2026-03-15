# list_item.py
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

from copy import deepcopy
from gi.repository import Adw
from gi.repository import Gtk

from ....core.utils import isiterable

from .dropdown import *
from .entry import *

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