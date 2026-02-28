# database_add_sqlite_view.py
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
from gi.repository import Gtk

@Gtk.Template(resource_path = '/com/wittara/studio/database_add_sqlite_view.ui')
class DatabaseAddSQLiteView(Adw.PreferencesPage):

    __gtype_name__ = 'DatabaseAddSQLiteView'

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

    def get_config(self) -> dict:
        """"""
        database = self.Database.get_text()
        alias    = self.Alias.get_text()

        database = database.strip()
        alias    = alias.strip() or _('New Connection')

        return {'database': database,
                'alias':    alias}

    def on_connect(self) -> None:
        """"""
        def do_connect() -> None:
            """"""
            config = self.get_config()

            from .core.connection_manager import ConnectionManager
            success, message = ConnectionManager.check_connection('sqlite', config)

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

    @Gtk.Template.Callback()
    def _on_database_clicked(self,
                             button: Gtk.Button,
                             ) ->    None:
        """"""
        FILTER_SQLITE = Gtk.FileFilter()
        FILTER_SQLITE.set_name(_('SQLite Files'))
        FILTER_SQLITE.add_pattern('*.sqlite')
        FILTER_SQLITE.add_pattern('*.db')
        FILTER_SQLITE.add_mime_type('application/vnd.sqlite3')

        FILTER_ALL = Gtk.FileFilter()
        FILTER_ALL.set_name(_('All Files'))
        FILTER_ALL.add_pattern('*')

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(FILTER_SQLITE)
        filters.append(FILTER_ALL)

        dialog = Gtk.FileDialog()
        dialog.set_title(_('Open'))
        dialog.set_modal(True)
        dialog.set_filters(filters)

        def on_dialog_dismissed(dialog: Gtk.FileDialog,
                                result: Gio.Task,
                                ) ->    None:
            """"""
            if result.had_error():
                return

            file = dialog.open_finish(result)
            self.Database.set_text(file.get_path())

            if self.Alias.get_text() == _('New Connection'):
                from os.path import basename
                from os.path import splitext
                filename = basename(file.get_path())
                filename = splitext(filename)[0]
                self.Alias.set_text(filename)

        window = self.get_root()
        dialog.open(window, None, on_dialog_dismissed)
