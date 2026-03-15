# sheet.py
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

from gi.repository import Gtk

import gc
import logging

from ._template import NodeTemplate
from ._utils    import iscompatible
from ._utils    import isdatatable
from ._utils    import isreconnected
from ._utils    import take_snapshot

from ....core.construct import Sheet
from ....core.utils     import unique_name

from ..content import NodeContent
from ..frame   import NodeFrame
from ..socket  import NodeSocket
from ..socket  import NodeSocketType
from ..widgets import NodeLabel
from ..widgets import NodeSpinButton

logger = logging.getLogger(__name__)

class NodeSheet(NodeTemplate):

    ndname = _('Sheet')

    action = 'new-sheet'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeSheet(x, y)

        self.frame.has_data   = self.has_data
        self.frame.has_view   = self.has_view
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['replace-tables'] = {}

        self._add_output()
        self._add_input()

        return self.frame

    def has_data(self) -> bool:
        """"""
        contents = self.frame.contents[:-1]
        for content in contents:
            if not content.Socket:
                continue
            if content.Socket.is_input():
                return True
        return False

    def has_view(self) -> bool:
        """"""
        from .viewer import NodeViewer
        content = self.frame.contents[0]
        for link in content.Socket.links:
            if not link.compatible:
                continue
            frame = link.out_socket.Frame
            if isinstance(frame.parent, NodeViewer):
                return True
        return False

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        value = self.frame.data['value']
        value.tables = {}
        value.sparse = {}
        # TODO: preserve manual input

        for self_content in self.frame.contents[1:-1]:
            box = self_content.Widget
            label = box.get_first_child()
            old_title = label.get_label()
            if old_title not in self.frame.data:
                continue

            if links := self_content.Socket.links:
                psocket = links[0].in_socket
                pcontent = psocket.Content
                pdata = pcontent.get_data()
                coord = self.frame.data[old_title]
                is_table = isdatatable(pdata)

                if is_table:
                    value.tables[old_title] = (coord, pdata)
                else:
                    value.sparse[coord] = pdata

                self._rename_label(self_content, label, old_title, is_table)

    def do_save(self) -> list:
        """"""
        values = []
        for content in self.frame.contents[1:-1]:
            box = content.Widget
            label = box.get_first_child()
            title = label.get_label()
            position = self.frame.data[title]
            value = {
                'title':    title,
                'position': position,
            }
            values.append(value)
        return values

    def do_restore(self,
                   values: list,
                   ) ->    None:
        """"""
        try:
            for index, value in enumerate(values):
                index += 1 # input socket starts from index 1
                n_ready_inputs = len(self.frame.contents) - 2
                if index <= n_ready_inputs:
                    widget = self.frame.contents[index].Widget
                    widget.set_data(value['position'])
                else:
                    tables = self.frame.data['replace-tables']
                    tables[index] = value
        except Exception as e:
            logger.error(e, exc_info = True)
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

        self.frame.do_execute(backward = False)

    def _add_output(self) -> None:
        """"""
        self.frame.data['value'] = Sheet()

        def get_data() -> Sheet:
            """"""
            return self.frame.data['value']

        def set_data(value: Sheet) -> None:
            """"""
            self.frame.data['value'] = value
            self.frame.do_execute(backward = False)

        widget = NodeLabel(_('Sheet'))
        socket_type = NodeSocketType.OUTPUT
        self.frame.add_content(widget      = widget,
                               socket_type = socket_type,
                               data_type   = Sheet,
                               get_data    = get_data,
                               set_data    = set_data)

    def _add_input(self) -> None:
        """"""
        widget = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        widget.set_data = lambda *_: None

        label = NodeLabel(_('Value'))
        label.set_xalign(0.0)
        label.set_opacity(0.0)
        widget.append(label)

        socket_type = NodeSocketType.INPUT
        content = self.frame.add_content(widget      = widget,
                                         socket_type = socket_type,
                                         placeholder = True,
                                         auto_remove = True)

        # TODO: placeholder implementation is currently so fragile,
        # both in NodeSheet and NodeViewer. It is so ugly as we mix
        # up logical state and UI state.

        def restore_data(title:   str,
                         content: NodeContent,
                         ) ->     str:
            """"""
            cindex = self.frame.contents.index(content)
            tables = self.frame.data['replace-tables']
            if cindex in tables:
                title = tables[cindex]['title']
                position = tables[cindex]['position']
                label.set_label(title)
                self.frame.data[title] = tuple(position)
                del tables[cindex]
            return title

        def replace_widget(title: str) -> None:
            """"""
            container = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
            container.add_css_class('linked')

            if title not in self.frame.data:
                self.frame.data[title] = (1, 1) # column, row

            get_title = lambda: label.get_label()

            spin_col = self._add_col_spin(get_title)
            spin_row = self._add_row_spin(get_title)

            container.append(spin_col)
            container.append(spin_row)

            expander = Gtk.Expander(label = label.get_label(),
                                    child = container)
            widget.append(expander)

            label.bind_property('label', expander, 'label')

            def set_data(value: tuple) -> None:
                """"""
                col, row = value
                spin_col.set_data(col)
                spin_row.set_data(row)
                self.frame.data[get_title()] = value

            widget.set_data = set_data

            label.set_visible(False)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            widget = self_content.Widget
            label = widget.get_first_child()

            old_title = label.get_label()
            new_title = old_title

            # Auto-generate the socket label if needed
            if not self_content.is_freezing:
                pdata = pair_socket.Content.get_data()

                titles = [
                    content.Widget.get_first_child().get_label()
                    for content in self.frame.contents[1:-1]
                    if  content != self_content
                ]
                if isdatatable(pdata):
                    new_title = unique_name(_('Table'), titles)
                else:
                    new_title = unique_name(_('Value'), titles)

                label.set_label(new_title)
                label.set_opacity(1.0)

            if not iscompatible(pair_socket, self_content):
                if self_content.placeholder:
                    self_content.placeholder = False
                    self_content.Socket.placeholder = False
                    self._add_input()
                return

            if isreconnected(pair_socket, self_content):
                pdata = pair_socket.Content.get_data()
                is_table = isdatatable(pdata)
                self._rename_label(self_content, label, old_title, is_table)

                return # skip if the pending socket to be removed
                       # get connected again to the previous node

            new_title = restore_data(new_title, self_content)

            if self_content.placeholder:
                self_content.placeholder = False
                self_content.Socket.placeholder = False
                replace_widget(new_title)
                self._add_input()

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_remove(content: NodeContent) -> None:
            """"""
            title = label.get_label()
            if title in self.frame.data:
                del self.frame.data[title]

            content.node_uid = None
            self.frame.remove_content(content)

            del content
            gc.collect()

        content.do_remove = do_remove

    def _rename_label(self,
                      self_content: NodeContent,
                      label:        Gtk.Label,
                      old_title:    str,
                      is_table:     bool,
                      ) ->          None:
        """"""
        new_title = old_title
        titles = [
            content.Widget.get_first_child().get_label()
            for content in self.frame.contents[1:-1]
            if  content != self_content
        ]
        if old_title.startswith(_('Value')) and is_table:
            new_title = unique_name(_('Table'), titles)
        if old_title.startswith(_('Table')) and not is_table:
            new_title = unique_name(_('Value'), titles)
        self.frame.data[new_title] = self.frame.data.pop(old_title)
        label.set_label(new_title)

    def _add_col_spin(self,
                      get_title: callable,
                      ) ->       NodeSpinButton:
        """"""
        def get_data() -> int:
            """"""
            return self.frame.data[get_title()][0]

        def set_data(value: int) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                _, row = self.frame.data[get_title()]
                self.frame.data[get_title()] = (value, row)
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        spin = NodeSpinButton(title    = _('Column'),
                              get_data = get_data,
                              set_data = set_data,
                              lower    = 1,
                              digits   = 0)

        return spin

    def _add_row_spin(self,
                      get_title: callable,
                      ) ->       NodeSpinButton:
        """"""
        def get_data() -> int:
            """"""
            return self.frame.data[get_title()][1]

        def set_data(value: int) -> None:
            """"""
            def callback(value: int) -> None:
                """"""
                col, _ = self.frame.data[get_title()]
                self.frame.data[get_title()] = (col, value)
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        spin = NodeSpinButton(title    = _('Row'),
                              get_data = get_data,
                              set_data = set_data,
                              lower    = 1,
                              digits   = 0)

        return spin