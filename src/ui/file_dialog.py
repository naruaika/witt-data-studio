# file_dialog.py
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

from gi.repository import Gio
from gi.repository import Gtk
from typing        import Any

class FileDialog():

    @staticmethod
    def open(window:   'Window',
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
                                modal   = False,
                                filters = filters)

        def on_dismissed(dialog: Gtk.FileDialog,
                         result: Gio.Task,
                         ) ->    None:
            """"""
            if result.had_error():
                return

            file = dialog.open_finish(result)
            file_path = file.get_path()

            application = window.get_application()
            application.load_file(file_path, callback)

        dialog.open(window, None, on_dismissed)

    @staticmethod
    def save(file_path: 'str',
             content:   'Any',
             callback:  'callable',
             ) ->       'None':
        """"""
        from ..backend.file import File
        File.write(file_path, content)

        callback(True, file_path)

    @staticmethod
    def save_as(file_name: 'str',
                content:   'Any',
                window:    'Window',
                callback:  'callable',
                ) ->       'None':
        """"""
        dialog = Gtk.FileDialog(title        = _('Save As'),
                                modal        = True,
                                initial_name = file_name)

        def on_dismissed(dialog: Gtk.FileDialog,
                         result: Gio.Task,
                         ) ->    None:
            """"""
            if result.had_error():
                callback(False, None)
                return

            file = dialog.save_finish(result)
            file_path = file.get_path()

            FileDialog.save(file_path, content, callback)

        dialog.save(window, None, on_dismissed)

from .window.widget import Window
