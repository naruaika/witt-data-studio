# database_add_postgresql_view.py
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
from gi.repository import GLib
from gi.repository import Gtk

@Gtk.Template(resource_path = '/com/wittara/studio/database_add_postgresql_view.ui')
class DatabaseAddPostgreSQLView(Adw.PreferencesPage):

    __gtype_name__ = 'DatabaseAddPostgreSQLView'

    Host     = Gtk.Template.Child()
    Port     = Gtk.Template.Child()
    Username = Gtk.Template.Child()
    Password = Gtk.Template.Child()
    Database = Gtk.Template.Child()
    Alias    = Gtk.Template.Child()

    def __init__(self,
                 Button:  Gtk.Button,
                 Spinner: Gtk.Spinner,
                 ) ->     None:
        """"""
        super().__init__()

        self.Button  = Button
        self.Spinner = Spinner

        self._password = ''

    def set_password(self,
                     password: str,
                     ) ->      None:
        """"""
        self._password = password

    def get_config(self) -> dict:
        """"""
        host     = self.Host.get_text()
        port     = self.Port.get_value()
        username = self.Username.get_text()
        password = self.Password.get_text()
        database = self.Database.get_text()
        alias    = self.Alias.get_text()

        host     = host.strip()     or 'localhost'
        port     = int(port)        or 5432
        username = username.strip() or 'postgres'
        password = password         or self._password
        database = database.strip()
        alias    = alias.strip()    or _('New Connection')

        return {'host':     host,
                'port':     port,
                'username': username,
                'password': password,
                'database': database,
                'alias':    alias}

    def on_connect(self) -> None:
        """"""
        def do_connect() -> None:
            """"""
            config = self.get_config()

            from .core.connection_manager import ConnectionManager
            success, message = ConnectionManager.check_connection('postgresql', config)

            banner = Adw.Banner(title = message, revealed = True)

            if not success:
                banner.set_button_label(_('Retry'))
                banner.connect('button-clicked', lambda *_: self.on_connect())

            from time import sleep
            sleep(0.15) # near instantly error can confuse users
                        # especially when the same error occurs;
                        # a slight delay may help them notice it

            GLib.idle_add(self.set_banner, banner)
            GLib.idle_add(self.Spinner.set_visible, False)
            GLib.idle_add(self.Button.set_sensitive, True)

        self.set_banner(None)
        self.Spinner.set_visible(True)
        self.Button.set_sensitive(False)

        from threading import Thread
        Thread(target = do_connect, daemon = True).start()
