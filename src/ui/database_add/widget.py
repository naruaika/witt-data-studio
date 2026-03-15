# database_add_window.py
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

from gi.repository import Adw
from gi.repository import Gdk
from gi.repository import Gtk

@Gtk.Template(resource_path = '/com/wittara/studio/ui/database_add/template.ui')
class DatabaseAddWindow(Adw.Window):

    __gtype_name__ = 'DatabaseAddWindow'

    WindowTitle    = Gtk.Template.Child()
    MainContainer  = Gtk.Template.Child()

    ConnectButton  = Gtk.Template.Child()
    ConnectSpinner = Gtk.Template.Child()

    def __init__(self,
                 dialect:  str,
                 callback: callable,
                 **kwargs: dict,
                 ) ->      None:
        """"""
        super().__init__(**kwargs)

        self.dialect  = dialect
        self.callback = callback

        self._setup_uinterfaces()
        self._setup_controllers()

    def set_data(self,
                 config: dict,
                 ) ->    None:
        """"""
        match self.dialect:
            case 'mysql':
                self.view.Host.set_text(    config.get('host', ''))
                self.view.Port.set_value(   config.get('port', 1))
                self.view.Database.set_text(config.get('database', ''))
                self.view.Username.set_text(config.get('username', ''))
                self.view.Password.set_text(config.get('password', ''))
                self.view.Alias.set_text(   config.get('alias', ''))

            case 'postgresql':
                self.view.Host.set_text(    config.get('host', ''))
                self.view.Port.set_value(   config.get('port', 1))
                self.view.Database.set_text(config.get('database', ''))
                self.view.Username.set_text(config.get('username', ''))
                self.view.Password.set_text(config.get('password', ''))
                self.view.Alias.set_text(   config.get('alias', ''))

            case 'sqlite':
                self.view.Database.set_text(config.get('database', ''))
                self.view.Alias.set_text(   config.get('alias', ''))

            case 'duckdb':
                self.view.Database.set_text(config.get('database', ''))
                self.view.Alias.set_text(   config.get('alias', ''))

        title = _('Edit Connection')
        self.WindowTitle.set_title(title)
        self.set_title(title)

        alias = config.get('alias', _('Unknown'))
        subtitle = self.WindowTitle.get_subtitle()
        subtitle = f'{alias} @ {subtitle}'
        self.WindowTitle.set_subtitle(subtitle)

    def set_password(self,
                     password: str,
                     ) ->      None:
        """"""
        if hasattr(self.view, 'set_password'):
            self.view.set_password(password)

    def _setup_uinterfaces(self) -> None:
        """"""
        match self.dialect:
            case 'mysql':
                from .view_mysql import DatabaseAddMySQLView
                self.view = DatabaseAddMySQLView(self.ConnectButton,
                                                 self.ConnectSpinner)
                self.WindowTitle.set_subtitle('MySQL')

            case 'postgresql':
                from .view_postgresql import DatabaseAddPostgreSQLView
                self.view = DatabaseAddPostgreSQLView(self.ConnectButton,
                                                      self.ConnectSpinner)
                self.WindowTitle.set_subtitle('PostgreSQL')

            case 'sqlite':
                from .view_sqlite import DatabaseAddSQLiteView
                self.view = DatabaseAddSQLiteView(self.ConnectButton,
                                                  self.ConnectSpinner)
                self.WindowTitle.set_subtitle('SQLite')

            case 'duckdb':
                from .view_duckdb import DatabaseAddDuckDBView
                self.view = DatabaseAddDuckDBView(self.ConnectButton,
                                                  self.ConnectSpinner)
                self.WindowTitle.set_subtitle('DuckDB')

        self.MainContainer.set_child(self.view)
        self.on_connect = self.view.on_connect

        # Disable scroll to focus behavior of the Gtk.Viewport
        scrolled_window = self.view.get_first_child()
        viewport = scrolled_window.get_first_child()
        viewport.set_scroll_to_focus(False)

        # Make the window resize its height dynamically
        scrolled_window.set_propagate_natural_height(True)

    def _setup_controllers(self) -> None:
        """"""
        controller = Gtk.EventControllerKey()
        controller.connect('key-pressed', self._on_key_pressed)
        self.add_controller(controller)

    def _on_key_pressed(self,
                        event:   Gtk.EventControllerKey,
                        keyval:  int,
                        keycode: int,
                        state:   Gdk.ModifierType,
                        ) ->     bool:
        """"""
        if state & Gdk.ModifierType.CONTROL_MASK and \
                keyval == Gdk.KEY_Escape:
            self.close()
            return Gdk.EVENT_STOP

        if keyval == Gdk.KEY_F5:
            self.on_connect()
            return Gdk.EVENT_STOP

        return Gdk.EVENT_PROPAGATE

    @Gtk.Template.Callback()
    def _on_connect_button_clicked(self,
                                   button: Gtk.Button,
                                   ) ->    None:
        """"""
        self.on_connect()

    @Gtk.Template.Callback()
    def _on_save_button_clicked(self,
                                button: Gtk.Button,
                                ) ->    None:
        """"""
        config = self.view.get_config()
        self.callback(config)
        self.close()
