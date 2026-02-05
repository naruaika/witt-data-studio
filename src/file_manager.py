# file_manager.py
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

from gi.repository import Gio
from gi.repository import Gtk
from typing import Any

class FileManager():

    @staticmethod
    def open_file(window:   'Window',
                  callback: 'callable' = None,
                  ) ->      'None':
        """"""
        FILTER_WITT = Gtk.FileFilter()
        FILTER_WITT.set_name('Witt Books')
        FILTER_WITT.add_pattern('*.wibook')

        FILTER_TEXT = Gtk.FileFilter()
        FILTER_TEXT.set_name(_('Text Files'))
        FILTER_TEXT.add_pattern('*.csv')
        FILTER_TEXT.add_pattern('*.tsv')
        FILTER_TEXT.add_pattern('*.txt')
        FILTER_TEXT.add_pattern('*.json')
        FILTER_TEXT.add_mime_type('text/csv')
        FILTER_TEXT.add_mime_type('text/tsv')
        FILTER_TEXT.add_mime_type('text/plain')
        FILTER_TEXT.add_mime_type('application/json')

#       FILTER_SHEET = Gtk.FileFilter()
#       FILTER_SHEET.set_name(_('Spreadsheet Files'))
#       FILTER_SHEET.add_pattern('*.xls')
#       FILTER_SHEET.add_pattern('*.xlsx')
#       FILTER_SHEET.add_pattern('*.xlsm')
#       FILTER_SHEET.add_pattern('*.xlsb')
#       FILTER_SHEET.add_pattern('*.xla')
#       FILTER_SHEET.add_pattern('*.xlam')
#       FILTER_SHEET.add_pattern('*.ods')
#       FILTER_SHEET.add_mime_type('application/vnd.ms-excel')
#       FILTER_SHEET.add_mime_type('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
#       FILTER_SHEET.add_mime_type('application/vnd.ms-excel.sheet.macroEnabled.12')
#       FILTER_SHEET.add_mime_type('application/vnd.ms-excel.sheet.binary.macroEnabled.12')
#       FILTER_SHEET.add_mime_type('application/vnd.ms-excel.addin.macroEnabled.12')
#       FILTER_SHEET.add_mime_type('application/vnd.oasis.opendocument.spreadsheet')

        FILTER_PARQUET = Gtk.FileFilter()
        FILTER_PARQUET.set_name(_('Parquet Files'))
        FILTER_PARQUET.add_pattern('*.parquet')
        FILTER_PARQUET.add_mime_type('application/vnd.apache.parquet')

        # This option is not intended to be used by the users to force
        # opening unsupported files. Instead, it can be used for example
        # to verify whether they are in the right directory or to see
        # whether the file exists but it's not currently supported.
        FILTER_ALL = Gtk.FileFilter()
        FILTER_ALL.set_name(_('All Files'))
        FILTER_ALL.add_pattern('*')

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(FILTER_ALL)
        filters.append(FILTER_WITT)
        filters.append(FILTER_TEXT)
#       filters.append(FILTER_SHEET)
        filters.append(FILTER_PARQUET)

        dialog = Gtk.FileDialog(title   = _('Open'),
                                modal   = True,
                                filters = filters)

        def on_dialog_dismissed(dialog: Gtk.FileDialog,
                                result: Gio.Task,
                                ) ->    None:
            """"""
            if result.had_error():
                return

            file = dialog.open_finish(result)
            file_path = file.get_path()

            application = window.get_application()
            application.load(file_path, callback)

        dialog.open(window, None, on_dialog_dismissed)

    @staticmethod
    def save_file(file_path: 'str',
                  content:   'Any',
                  callback:  'callable',
                  ) ->       'None':
        """"""
        from .core.file_manager import FileManager
        FileManager.write_file(file_path, content)

        callback(True, file_path)

    @staticmethod
    def save_file_as(file_name: 'str',
                     content:   'Any',
                     window:    'Window',
                     callback:  'callable',
                     ) ->       'None':
        """"""
        dialog = Gtk.FileDialog(title        = _('Save As'),
                                modal        = True,
                                initial_name = file_name)

        def on_dialog_dismissed(dialog: Gtk.FileDialog,
                                result: Gio.Task,
                                ) ->    None:
            """"""
            if result.had_error():
                callback(False, None)
                return

            file = dialog.save_finish(result)
            file_path = file.get_path()

            FileManager.save_file(file_path, content, callback)

        dialog.save(window, None, on_dialog_dismissed)

from .window import Window
