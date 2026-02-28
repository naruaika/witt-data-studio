# database_add_window.py
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
from gi.repository import Gdk
from gi.repository import Gtk

@Gtk.Template(resource_path = '/com/wittara/studio/database_add_window.ui')
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
                self.view.Host.set_text(config.get('host', ''))
                self.view.Port.set_value(config.get('port', 1))
                self.view.Database.set_text(config.get('database', ''))
                self.view.Username.set_text(config.get('username', ''))
                self.view.Password.set_text(config.get('password', ''))
                self.view.Alias.set_text(config.get('alias', ''))

            case 'postgresql':
                self.view.Host.set_text(config.get('host', ''))
                self.view.Port.set_value(config.get('port', 1))
                self.view.Database.set_text(config.get('database', ''))
                self.view.Username.set_text(config.get('username', ''))
                self.view.Password.set_text(config.get('password', ''))
                self.view.Alias.set_text(config.get('alias', ''))

            case 'sqlite':
                self.view.Database.set_text(config.get('database', ''))
                self.view.Alias.set_text(config.get('alias', ''))

            case 'duckdb':
                self.view.Database.set_text(config.get('database', ''))
                self.view.Alias.set_text(config.get('alias', ''))

        title = _('Edit Connection')
        self.WindowTitle.set_title(title)
        self.set_title(title)

        alias = config.get('alias', _('Unknown'))
        subtitle = self.WindowTitle.get_subtitle()
        subtitle = f'{alias} – {subtitle}'
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
                from .database_add_mysql_view import DatabaseAddMySQLView
                self.view = DatabaseAddMySQLView(self.ConnectButton,
                                                 self.ConnectSpinner)
                self.WindowTitle.set_subtitle('MySQL')

            case 'postgresql':
                from .database_add_postgresql_view import DatabaseAddPostgreSQLView
                self.view = DatabaseAddPostgreSQLView(self.ConnectButton,
                                                      self.ConnectSpinner)
                self.WindowTitle.set_subtitle('PostgreSQL')

            case 'sqlite':
                from .database_add_sqlite_view import DatabaseAddSQLiteView
                self.view = DatabaseAddSQLiteView(self.ConnectButton,
                                                  self.ConnectSpinner)
                self.WindowTitle.set_subtitle('SQLite')

            case 'duckdb':
                from .database_add_duckdb_view import DatabaseAddDuckDBView
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
