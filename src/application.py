# application.py
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

from argparse      import ArgumentParser
from gi.repository import Adw
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gtk
from typing        import Callable

import logging

from .ui.window.widget import Window

logger = logging.getLogger(__name__)

class Application(Adw.Application):
    """The main application singleton class."""

    APP_ID  = 'com.wittara.studio'
    VERSION = '0.1.0'

    WORKBOOK_FORMATS = ['wibook']
    WIBOOK_VERSION   = '1.0'

    def __init__(self,
                 app_id:  str,
                 version: str,
                 ) ->     None:
        """"""
        self.APP_ID  = app_id
        self.VERSION = version

        flags = Gio.ApplicationFlags.HANDLES_COMMAND_LINE | \
                Gio.ApplicationFlags.HANDLES_OPEN
        super().__init__(application_id     = self.APP_ID,
                         flags              = flags,
                         resource_base_path = '/com/wittara/studio')

        self._setup_actions()
        self._setup_controllers()
        self._setup_libraries()

    def do_activate(self) -> None:
        """"""
        window = self.get_active_main_window()

        if not window:
            logger.info('Spawning a new main window...')
            window = Window(application = self)

        window.present()

    def do_command_line(self,
                        command_line: Gio.ApplicationCommandLine,
                        ) ->          int:
        """"""
        logger.info('Starting up application from command line...')

        parser = self._create_argument_parser()

        try:
            args = parser.parse_args(command_line.get_arguments()[1:])
            logger.debug(f'Parsed command line arguments: {args}')

        except SystemExit:
            pass # ignore unrecognized arguments

        else:
            self._load_files_on_startup(args.paths)

        self.activate()

        return 0

    def _create_argument_parser(self) -> ArgumentParser:
        """"""
        description = _('A powerful, user-friendly, and integrated data platform.')
        parser = ArgumentParser(prog        = 'witt-data-studio',
                                usage       = '%(prog)s [options] [paths...]',
                                description = description)

        parser.add_argument('paths',
                            nargs = '*',
                            help  = _('path to supported files'))

        return parser

    def do_open(self,
                files:   list[Gio.File],
                n_files: int,
                hint:    str,
                ) ->     None:
        """"""
        logger.info('Starting up application from file open...')

        paths = [path for file in files if (path := file.get_path())]

        self._load_files_on_startup(paths)

        self.activate()

    def _load_files_on_startup(self,
                               paths: list[str],
                               ) ->   None:
        """"""
        for file_path in paths:
            self.load_file(file_path, on_startup = True)

    def do_shutdown(self) -> None:
        """"""
        logger.info('Shutting down application...')

        self._delete_temporary_files()

        Gio.Application.do_shutdown(self)

    def _delete_temporary_files(self) -> None:
        """"""
        import glob
        import os
        import tempfile

        dir_path = tempfile.gettempdir()
        pathname = os.path.join(dir_path, '*.wisnap')

        for file_path in glob.glob(pathname):
            try:
                logger.debug(f'Deleting temporary file: {file_path}')
                os.remove(file_path)

            except Exception as e:
                logger.error(e, exc_info = True)

    def _setup_actions(self) -> None:
        """"""
        self.create_action('copy-to-clipboard', callback   = self._on_copy_to_clipboard_action,
                                                param_type = GLib.VariantType('s'))

        self.create_action('about',             self._on_about_action,
                                                ['F12'])
        self.create_action('exit',              self._on_exit_action,
                                                ['<Primary>q'])

        self.create_action('new-window',        self._on_new_window_action,
                                                ['<Shift><Primary>N'])

        self.create_action('open-file',         self._on_open_file_action,
                                                ['<Primary>o'])
        self.create_action('open-database',     self._on_open_database_action,
                                                ['<Shift><Primary>o'])

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

    def _on_copy_to_clipboard_action(self,
                                     action:    Gio.SimpleAction,
                                     parameter: GLib.Variant,
                                     ) ->       None:
        """"""
        content = parameter.get_string()

        display = Gdk.Display.get_default()
        clipboard = display.get_clipboard()

        clipboard.set(GObject.Value(str, content))
        logger.info(f'Copied to clipboard: {content}')

    def _on_about_action(self,
                         action:    Gio.SimpleAction,
                         parameter: GLib.Variant,
                         ) ->       None:
        """"""
        logger.info('Showing application about dialog...')

        repository_url = 'https://github.com/naruaika/witt-data-studio'
        dialog = Adw.AboutDialog(application_name   = 'Witt Data Studio',
                                 application_icon   = self.APP_ID,
                                 version            = self.VERSION,
                                 copyright          = '© 2025 Naufan Rusyda Faikar',
                                 license_type       = Gtk.License.APACHE_2_0,
                                 designers          = ['Naufan Rusyda Faikar <hello@naruaika.me>'],
                                 developer_name     = 'Naufan Rusyda Faikar',
                                 developers         = ['Naufan Rusyda Faikar <hello@naruaika.me>'],
                                 artists            = ['Naufan Rusyda Faikar <hello@naruaika.me>'],
                                 issue_url          = f'{repository_url}/issues',
                                 support_url        = f'{repository_url}/discussions',
                                 translator_credits = _('translator-credits'),
                                 website            = repository_url)

        window = self.get_active_main_window()
        dialog.present(window)

    def _on_exit_action(self,
                        action:    Gio.SimpleAction,
                        parameter: GLib.Variant,
                        ) ->       None:
        """"""
        logger.info('Exiting application...')
        for window in self.get_windows():
            window.close()

    def _on_new_window_action(self,
                              action:    Gio.SimpleAction,
                              parameter: GLib.Variant,
                              ) ->       None:
        """"""
        logger.info('Spawning a new main window...')
        window = Window(application = self)
        window.present()

    def _on_open_file_action(self,
                             action:    Gio.SimpleAction,
                             parameter: GLib.Variant,
                             ) ->       None:
        """"""
        logger.info('Showing open file dialog...')

        from .ui.file_dialog import FileDialog
        window = self.get_active_main_window()
        FileDialog.open(window)

    def _on_open_database_action(self,
                                 action:    Gio.SimpleAction,
                                 parameter: GLib.Variant,
                                 ) ->       None:
        """"""
        logger.info('Showing open database dialog...')

        from .ui.database_import.widget import DatabaseImportWindow
        window = self.get_active_main_window()
        window = DatabaseImportWindow(transient_for = window,
                                      application   = self)
        window.present()

    def _setup_controllers(self) -> None:
        """"""
        self.connect('window-removed', self._on_window_removed)

    def _on_window_removed(self,
                           application: Gtk.Application,
                           window:      Gtk.Window,
                           ) ->         None:
        """"""
        # Closing all transient windows
        for target in self.get_windows():
            if target.get_transient_for() == window:
                target.close()

    def _setup_libraries(self) -> None:
        """"""
        import locale
        locale.setlocale(locale.LC_ALL, '')

        from gi.events import GLibEventLoopPolicy
        import asyncio
        policy = GLibEventLoopPolicy()
        asyncio.set_event_loop_policy(policy)

        from gi.repository import GtkSource
        from gi.repository import WebKit
        GObject.type_register(GtkSource.View)
        GObject.type_register(WebKit.WebView)

        from .ui.status_bar.widget         import StatusBar
        from .ui.toolbar.widget            import Toolbar
        from .editors.node.canvas          import NodeCanvas
        from .editors.node.ui.minimap      import NodeMinimap
        from .editors.sheet.canvas         import SheetCanvas
        from .editors.sheet.ui.formula_bar import SheetFormulaBar
        GObject.type_register(StatusBar)
        GObject.type_register(Toolbar)
        GObject.type_register(NodeCanvas)
        GObject.type_register(NodeMinimap)
        GObject.type_register(SheetCanvas)
        GObject.type_register(SheetFormulaBar)

        from polars import Config
        Config.set_tbl_width_chars(-1)
        Config.set_fmt_str_lengths(20)

        from .plugins import polars
        polars.initialize()

    def load_file(self,
                  file_path:  str,
                  callback:   callable = None,
                  on_startup: bool     = False,
                  ) ->        None:
        """"""
        logger.info(f'Loading file: {file_path}')

        from .core.utils import get_file_format
        file_format = get_file_format(file_path)

        if file_format not in self.WORKBOOK_FORMATS:
            self._load_source_file(file_path, callback, on_startup)
        else:
            self._load_workbook_file(file_path, on_startup)

        self.insert_recent_file_list(file_path)

    def _load_source_file(self,
                          file_path:  str,
                          callback:   callable = None,
                          on_startup: bool     = False,
                          ) ->        None:
        """"""
        if on_startup:
            window = Window(application = self)
        else:
            window = self.get_active_main_window()

        def do_launch() -> None:
            """"""
            from .ui.file_import.widget import FileImportWindow
            import_window = FileImportWindow(file_path     = file_path,
                                             callback      = callback,
                                             transient_for = window,
                                             application   = self)
            import_window.present()

        if on_startup:
            GLib.idle_add(do_launch)
        else:
            do_launch()

        window.present()

    def _load_workbook_file(self,
                            file_path:  str,
                            on_startup: bool = False,
                            ) ->        None:
        """"""
        from .backend.file       import File
        from .editors.node.frame import NodeFrame
        from .editors.node.link  import NodeLink

        content: dict = File.read(file_path)

        logger.debug(f'Parsed workbook file content: {content}')

        nodes:     list[NodeFrame]      = []
        links:     list[NodeLink]       = []
        instances: dict[int, NodeFrame] = {}

        schemas = content.get('nodes', [])
        self._create_nodes_from_schema(schemas, nodes, instances)

        schemas = content.get('links', [])
        self._create_links_from_schema(schemas, links, instances)

        if not on_startup:
            self._close_blank_main_window()

        # Get active viewer node
        viewer = None
        if node_id := content.get('viewer'):
            viewer = instances[node_id]

        # Get previous active tab page
        tab_page = content.get('tab_page')

        logger.info('Spawning a new main window...')
        window = Window(application = self,
                        nodes       = nodes,
                        links       = links,
                        viewer      = viewer,
                        tab_page    = tab_page,
                        file_path   = file_path)
        window.present()

    def get_recent_file_list(self) -> list[str]:
        """"""
        APP_ID = self.APP_ID.replace('.Devel', '')
        settings = Gio.Settings.new(APP_ID)

        from json import loads
        list_str = settings.get_string('recent-files')
        list_obj = loads(list_str)

        return list_obj

    def insert_recent_file_list(self,
                                file_path: str,
                                ) ->       None:
        """"""
        from json import dumps
        list_obj = self.get_recent_file_list()
        list_obj.insert(0, file_path)
        list_obj = list_obj[:500]
        list_obj = list(dict.fromkeys(list_obj))
        list_str = dumps(list_obj)

        APP_ID = self.APP_ID.replace('.Devel', '')
        settings = Gio.Settings.new(APP_ID)
        settings.set_string('recent-files', list_str)

    def _create_nodes_from_schema(self,
                                  schemas:   list,
                                  nodes:     list,
                                  instances: dict,
                                  ) ->       None:
        """"""
        from .editors.node.factory import create_new_node

        for schema in schemas:
            logger.debug(f'Creating node from schema: {schema}')

            try:
                node = create_new_node(schema['action'],
                                       schema['position'][0],
                                       schema['position'][1])
                node.do_restore(schema['contents'])
                nodes.append(node)

                instances[schema['id']] = node

            except Exception as e:
                logger.error(e, exc_info = True)

    def _create_links_from_schema(self,
                                  schemas:   list,
                                  links:     list,
                                  instances: dict,
                                  ) ->       None:
        """"""
        from .editors.node.content import NodeContent
        from .editors.node.frame   import NodeFrame
        from .editors.node.link    import NodeLink

        for schema in schemas:
            logger.debug(f'Creating node link from schema: {schema}')

            try:
                source: dict = schema['source']
                target: dict = schema['target']

                # Skip invalid links
                if source['node-id'] not in instances:
                    continue
                if target['node-id'] not in instances:
                    continue

                node1: NodeFrame = instances[source['node-id']]
                node2: NodeFrame = instances[target['node-id']]

                content1: NodeContent = node1.contents[source['content']]
                content2: NodeContent = node2.contents[target['content']]

                link = NodeLink(content1.Socket, content2.Socket).link()
                links.append(link)

            except Exception as e:
                logger.error(e, exc_info = True)

    def _close_blank_main_window(self) -> None:
        """"""
        window = self.get_active_main_window()
        if (
            not window.file_path          and
            not window.history.undo_stack and
            not window.history.redo_stack
        ):
            GLib.idle_add(window.close)

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
        logger.info('Saving file...')

        data = self._build_save_data(window)

        def on_finish(success:   bool,
                      file_path: str,
                      ) ->       None:
            """"""
            if success:
                window.file_path  = file_path
                window.file_saved = True
                window.StatusBar.set_file_saved(True)

        self._perform_save(window, file_path, data, on_finish)

        self.insert_recent_file_list(file_path)

    def _build_save_data(self,
                         window: Window,
                         ) ->    dict:
        """"""
        from time   import strftime
        from locale import getlocale

        from .editors.node.factory import NodeViewer

        tab_page = window.TabView.get_selected_page()
        tab_page = window.TabView.get_page_position(tab_page)

        data = {
            'version':  self.WIBOOK_VERSION,
            'timezone': strftime('%Z'), # TODO: should be configurable
            'locale':   getlocale(),    # TODO: should be configurable
            'nodes':    [],
            'links':    [],
            'viewer':   None,
            'tab_page': tab_page,
        }

        data['nodes'] = self._serialize_nodes(window)
        data['links'] = self._serialize_links(window)

        # Sort links for best reproducibility
        sort_key = lambda link: link['target']['content']
        data['links'] = sorted(data['links'], key = sort_key)

        # Get active viewer node
        for node in window.node_editor.nodes:
            if not isinstance(node.parent, NodeViewer):
                continue
            if node.is_active():
                data['viewer'] = id(node)
                break

        return data

    def _serialize_links(self,
                         window: Window,
                         ) ->    list[dict]:
        """"""
        from .editors.node.socket import NodeSocket

        def serialize_socket(socket: NodeSocket) -> dict:
            """"""
            contents = socket.Frame.contents
            return {
                'node-id': id(socket.Frame),
                'content': contents.index(socket.Content),
            }

        links = []

        for link in window.node_editor.links:
            links.append({
                'source': serialize_socket(link.in_socket),
                'target': serialize_socket(link.out_socket),
            })

        return links

    def _serialize_nodes(self,
                         window: Window,
                         ) ->    list[dict]:
        """"""
        nodes = []

        for node in window.node_editor.nodes:
            nodes.append({
                'id':       id(node),
                'action':   node.parent.action,
                'position': [node.x, node.y],
                'contents': node.do_save(),
            })

        return nodes

    def _perform_save(self,
                      window:    Window,
                      file_path: str,
                      data:      dict,
                      on_finish: Callable,
                      ) ->       None:
        """"""
        from .ui.file_dialog import FileDialog

        if file_path:
            FileDialog.save(file_path = file_path,
                            content   = data,
                            callback  = on_finish)

        else:
            file_name = '{}.wibook'.format(_('Book1'))
            FileDialog.save_as(file_name = file_name,
                               content   = data,
                               window    = window,
                               callback  = on_finish)

    def get_active_main_window(self) -> Window:
        """"""
        window = self.get_active_window()
        if not window:
            window = Window(application = self)
        while not isinstance(window, Window):
            window = window.get_transient_for()
        return window
