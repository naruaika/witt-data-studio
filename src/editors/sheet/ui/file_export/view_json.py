# view_json.py
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
from gi.repository import Gio
from gi.repository import Gtk

@Gtk.Template(resource_path = '/com/wittara/studio/editors/sheet/ui/file_export/view_json.ui')
class FileExportJSONView(Adw.PreferencesPage):

    __gtype_name__ = 'FileExportJSONView'

    ExportTo = Gtk.Template.Child()
    ExportAs = Gtk.Template.Child()

    @Gtk.Template.Callback()
    def _on_export_to_clicked(self,
                              button: Gtk.Button,
                              ) ->    None:
        """"""
        from pathlib import Path
        home_path = str(Path.home())
        home_path = Gio.File.new_for_path(home_path)

        dialog = Gtk.FileDialog(title          = _('Export To'),
                                initial_folder = home_path,
                                modal          = True)

        def on_dismissed(dialog: Gtk.FileDialog,
                         result: Gio.Task,
                         ) ->    None:
            """"""
            if result.had_error():
                return
            folder = dialog.select_folder_finish(result)
            self.ExportTo.set_text(folder.get_path())

        dialog.select_folder(self.get_root(), None, on_dismissed)