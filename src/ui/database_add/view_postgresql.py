# database_add_postgresql_view.py
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
from gi.repository import GLib
from gi.repository import Gtk

@Gtk.Template(resource_path = '/com/wittara/studio/ui/database_add/view_postgresql.ui')
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

            from ...backend.database import Database
            success, message = Database.check_connection('postgresql', config)

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
