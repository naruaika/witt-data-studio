# viewer.py
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
import gc
import logging

from ._template import NodeTemplate
from ._utils import isreconnected

from ....core.construct import Sheet
from ....core.utils import unique_name

from ..content import NodeContent
from ..frame import NodeFrame
from ..frame import NodeFrameType
from ..socket import NodeSocket
from ..socket import NodeSocketType

logger = logging.getLogger(__name__)

class NodeViewer(NodeTemplate):

    ndname = _('Viewer')

    action = 'new-viewer'

    SUPPORTED_VIEWS = {Sheet}

    PRIMITIVE_TYPES = {bool, float, int, str, list, dict, tuple}

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeViewer(x, y)

        self.frame.node_type  = NodeFrameType.TARGET
        self.frame.is_active  = self.is_active
        self.frame.set_active = self.set_active
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['is-active']      = False
        self.frame.data['replace-titles'] = {}

        self._add_input()

        self._setup_uinterfaces()

        return self.frame

    def _setup_uinterfaces(self) -> None:
        """"""
        self.frame.ActiveToggle.set_visible(True)

        def on_activated(button: Gtk.Button) -> None:
            editor = self.frame.get_editor()
            editor.select_viewer(self.frame)

        self.frame.ActiveToggle.connect('clicked', on_activated)

    def is_active(self) -> bool:
        """"""
        return self.frame.data['is-active']

    def set_active(self,
                   active: bool,
                   ) ->    None:
        """"""
        self.frame.data['is-active'] = active

        if active:
            self.frame.ActiveToggle.set_icon_name('view-reveal-symbolic')
            self.frame.ActiveToggle.remove_css_class('dimmed')
        else:
            self.frame.ActiveToggle.set_icon_name('view-conceal-symbolic')
            self.frame.ActiveToggle.add_css_class('dimmed')

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        if not pair_socket:
            return

        from polars import DataFrame
        from polars import LazyFrame
        from polars import Series

        pair_content = pair_socket.Content
        value = pair_content.get_data()

        for link in pair_socket.links:
            if link.out_socket.Frame != self.frame:
                continue
            self_content = link.out_socket.Content

            label = self_content.Widget

            label.remove_css_class('monospace')
            label.set_ellipsize(Pango.EllipsizeMode.END)
            label.set_wrap(False)

            if pair_socket.data_type == Sheet:
                if not self_content.Page:
                    continue
                editor = self_content.Page.get_child()
                editor.set_data(value.tables, value.sparse)

            elif pair_socket.data_type in self.PRIMITIVE_TYPES:
                label.set_label(str(value) or f'[{_('Empty')}]')
                label.set_ellipsize(Pango.EllipsizeMode.NONE)

                if pair_socket.data_type == str:
                    label.set_wrap(True)
                    label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)

            elif pair_socket.data_type in {DataFrame, LazyFrame, Series}:
                if isinstance(value, LazyFrame):
                    try:
                        value = value.collect()
                    except Exception as e:
                        value = e

                label.add_css_class('monospace')
                label.set_ellipsize(Pango.EllipsizeMode.NONE)
                label.set_label(str(value))

            elif value is None:
                label.set_label(f'[{_('None')}]')

            else:
                label.set_label(f'[{_('Object')}]')

    def do_save(self) -> list:
        """"""
        values = []
        for content in self.frame.contents[:-1]:
            label = content.Widget
            value = label.get_label()
            values.append(value)
        return values

    def do_restore(self,
                   values: list,
                   ) ->    None:
        """"""
        for index, value in enumerate(values):
            titles = self.frame.data['replace-titles']
            titles[index] = value

    def _add_input(self) -> None:
        """"""
        label = Gtk.Label(label     = _('Any'),
                          xalign    = 0.0,
                          opacity   = 0.0,
                          ellipsize = Pango.EllipsizeMode.END)
        label.add_css_class('node-label')
        socket_type = NodeSocketType.INPUT
        content = self.frame.add_content(label,
                                         socket_type,
                                         placeholder = True,
                                         auto_remove = True)

        def restore_data(title:   str,
                         content: NodeContent,
                         ) ->     str:
            """"""
            cindex = self.frame.contents.index(content)
            titles = self.frame.data['replace-titles']
            if cindex in titles:
                title = titles[cindex]
                label.set_label(title)
                del titles[cindex]
            return title

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            if isreconnected(pair_socket, self_content):
                if pair_socket.data_type in self.SUPPORTED_VIEWS:
                    return # skip if the pending socket to be removed
                           # get connected again to the previous node

            label = self_content.Widget
            title = label.get_label()

            if not self_content.is_freezing:
                if pair_socket.data_type in self.SUPPORTED_VIEWS:
                    # Auto-generate the socket label if needed
                    titles = [
                        content.Widget.get_label()
                        for content in self.frame.contents[:-1]
                        if  content != self_content
                    ]
                    title = pair_socket.data_type.__name__
                    title = unique_name(title, titles)
                    label.set_label(title)

            title = restore_data(title, self_content)

            label.set_opacity(1.0)

            if self_content.Page:
                window = self.frame.get_root()
                window.TabView.close_page(self_content.Page)
                self_content.Page = None

            if self.is_active():
                if pair_socket.data_type == Sheet:
                    args = (title, pair_socket, self_content)
                    GLib.idle_add(self.add_sheet_editor, *args)

            if self_content.placeholder:
                self_content.placeholder = False
                self_content.Socket.placeholder = False
                self._add_input()

            self.frame.do_execute(pair_socket,
                                  self_content,
                                  specified = True)

        content.do_link = do_link

        def do_remove(content: NodeContent) -> None:
            """"""
            content.node_uid = None

            self.frame.remove_content(content)

            if content.Page:
                window = self.frame.get_root()
                window.TabView.close_page(content.Page)
                content.Page = None

            del content
            gc.collect()

        content.do_remove = do_remove

    def add_sheet_editor(self,
                         title:        str,
                         pair_socket:  NodeSocket,
                         self_content: NodeContent,
                         ) ->          bool:
        """"""
        from ...sheet.editor import SheetEditor

        if not self.is_active():
            return Gdk.EVENT_PROPAGATE

        if window := self.frame.get_root():
            frame = pair_socket.Frame
            sheet = pair_socket.Content.get_data()
            editor = SheetEditor(sheet.tables,
                                 sheet.sparse,
                                 frame,
                                 title = title)
            self_content.Page = window.add_new_editor(editor)
            return Gdk.EVENT_PROPAGATE

        return Gdk.EVENT_STOP