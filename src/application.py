# application.py
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

from gi.repository import Adw
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gtk
from typing import Callable

from .window import Window

class Application(Adw.Application):
    """The main application singleton class."""

    WIBOOK_VERSION = '1.0'

    def __init__(self,
                 app_id:  str = 'com.macipra.witt',
                 version: str = '0.1.0',
                 ) ->     None:
        """"""
        self.APP_ID  = app_id
        self.VERSION = version

        super().__init__(application_id     = self.APP_ID,
                         flags              = Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
                         resource_base_path = '/com/macipra/witt')

        self._setup_actions()
        self._setup_controllers()
        self._setup_libraries()

    def do_activate(self) -> None:
        """"""
        window = self.get_active_window()

        if not window:
            window = Window(application = self)

        window.present()

    def do_command_line(self,
                        command_line: Gio.ApplicationCommandLine,
                        ) ->          int:
        """"""
        self.activate()

        return 0

    def create_action(self,
                      name:       str,
                      callback:   Callable,
                      shortcuts:  list[str]        = None,
                      param_type: GLib.VariantType = None,
                      ) ->        None:
        """"""
        action = Gio.SimpleAction.new(name, param_type)
        action.connect('activate', callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f'app.{name}', shortcuts)

    def _setup_actions(self) -> None:
        """"""
        self.create_action('about',     self._on_about_action,
                                        ['F12'])
        self.create_action('exit',      self._on_exit_action,
                                        ['<Primary>q'])

        self.create_action('open-file', self._on_open_file_action,
                                        ['<Primary>o'])

    def _on_about_action(self,
                         action:    Gio.SimpleAction,
                         parameter: GLib.Variant,
                         ) ->       None:
        """"""
        repository_url = 'https://github.com/naruaika/witt-data-studio'
        dialog = Adw.AboutDialog(application_name   = 'Witt Data Studio',
                                 application_icon   = self.APP_ID,
                                 version            = self.VERSION,
                                 copyright          = '© 2025 Naufan Rusyda Faikar',
                                 license_type       = Gtk.License.AGPL_3_0,
                                 designers          = ['Naufan Rusyda Faikar'],
                                 developer_name     = 'Naufan Rusyda Faikar',
                                 developers         = ['Naufan Rusyda Faikar'],
                                 issue_url          = f'{repository_url}/issues',
                                 support_url        = f'{repository_url}/discussions',
                                 translator_credits = _('translator-credits'))
        window = self.get_active_window()
        dialog.present(window)

    def _on_exit_action(self,
                        action:    Gio.SimpleAction,
                        parameter: GLib.Variant,
                        ) ->       None:
        """"""
        self.quit()

    def _on_open_file_action(self,
                             action:    Gio.SimpleAction,
                             parameter: GLib.Variant,
                             ) ->       None:
        """"""
        from .file_manager import FileManager
        window = self.get_active_main_window()
        FileManager.open_file(window)

    def _setup_controllers(self) -> None:
        """"""
        self.connect('window-removed', self._on_window_removed)

    def _on_window_removed(self,
                           application: Gtk.Application,
                           window:      Gtk.Window,
                           ) ->         None:
        """"""
        for _window in self.get_windows():
            if _window.get_transient_for() == window:
                _window.close()

    def _setup_libraries(self) -> None:
        """"""
        from gi.repository import GtkSource
        from gi.repository import WebKit
        from polars import Config
        from threading import Thread

        from .toolbar import Toolbar
        from .node.canvas import NodeCanvas
        from .node.minimap import NodeMinimap
        from .sheet.canvas import SheetCanvas

        GObject.type_register(GtkSource.View)
        GObject.type_register(WebKit.WebView)

        GObject.type_register(Toolbar)
        GObject.type_register(NodeCanvas)
        GObject.type_register(NodeMinimap)
        GObject.type_register(SheetCanvas)

        Config.set_tbl_width_chars(-1)
        Config.set_fmt_str_lengths(20)

        def do_preload() -> None:
            """"""
            from .core import plugin_repository
            from .core.parser_command_context import parser
            from .core.parser_sheet_formula import parser

        Thread(target = do_preload, daemon = False).start()

    def load(self,
             file_path: str,
             content:   dict,
             ) ->       None:
        """"""
        from .node.link import NodeLink
        from .node.repository import create_new_node

        nodes = []
        nodes_map = {}
        if 'nodes' in content:
            for schema in content['nodes']:
                try:
                    node = create_new_node(name = schema['action'],
                                           x    = schema['position'][0],
                                           y    = schema['position'][1])
                    node.do_restore(schema['contents'])
                    nodes.append(node)
                    nodes_map[schema['id']] = node
                except:
                    pass # TODO: show errors to user

        links = []
        if 'links' in content:
            for schema in content['links']:
                try:
                    source = schema['source']
                    target = schema['target']

                    if source['node-id'] not in nodes_map:
                        continue
                    if target['node-id'] not in nodes_map:
                        continue

                    node1 = nodes_map[source['node-id']]
                    node2 = nodes_map[target['node-id']]
                    content1 = node1.contents[source['content']]
                    content2 = node2.contents[target['content']]

                    link = NodeLink(content1.Socket, content2.Socket).link()
                    links.append(link)
                except:
                    pass # TODO: show errors to user

        window = Window(application = self,
                        nodes       = nodes,
                        links       = links)
        window.present()

        window.file_path = file_path

    def save(self,
             window: Window,
             ) ->    None:
        """"""
        self.save_as(window, window.file_path)

    def save_as(self,
                window:    Window,
                file_path: str = None,
                ) ->       None:
        """"""
        save_data = {'version': self.WIBOOK_VERSION}

        editor = window.node_editor

        save_data['nodes'] = []
        for node in editor.nodes:
            node_data = {
                'id':       id(node),
                'action':   node.parent.action,
                'position': [node.x, node.y],
                'contents': node.do_save(),
            }
            save_data['nodes'].append(node_data)

        save_data['links'] = []
        for link in editor.links:
            socket = link.in_socket
            source = {
                'node-id': id(socket.Frame),
                'content': socket.Frame.contents.index(socket.Content),
            }
            socket = link.out_socket
            target = {
                'node-id': id(socket.Frame),
                'content': socket.Frame.contents.index(socket.Content),
            }
            save_data['links'].append({
                'source': source,
                'target': target,
            })

        def do_finish(success:   bool,
                      file_path: str,
                      ) ->       None:
            """"""
            if success:
                window.file_path = file_path

        from .file_manager import FileManager

        if file_path:
            FileManager.save_file(file_path = file_path,
                                  content   = save_data,
                                  callback  = do_finish)
        else:
            FileManager.save_file_as(file_name = f'{_('Book')}1.wibook',
                                     content   = save_data,
                                     window    = window,
                                     callback  = do_finish)

    def get_active_main_window(self) -> Window:
        """"""
        window = self.get_active_window()
        while not isinstance(window, Window):
            window = window.get_transient_for()
        return window
