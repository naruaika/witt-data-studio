# file_export.py
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
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import Gtk

from .view_csv     import FileExportCSVView
from .view_json    import FileExportJSONView
from .view_parquet import FileExportParquetView

FORMAT_OPTS = {'csv':     'CSV',
               'parquet': 'Parquet',
               'json':    'JSON'}

@Gtk.Template(resource_path = '/com/wittara/studio/editors/sheet/ui/file_export/template.ui')
class FileExportWindow(Adw.Window):

    __gtype_name__ = 'FileExportWindow'

    FormatChooser = Gtk.Template.Child()
    MainContainer = Gtk.Template.Child()

    def __init__(self,
                 subtitle: str,
                 callback: callable,
                 **kwargs: dict,
                 ) ->      None:
        """"""
        super().__init__(**kwargs)

        self.subtitle = subtitle
        self.callback = callback

        self._setup_uinterfaces()
        self._setup_controllers()

    def _setup_uinterfaces(self) -> None:
        """"""
        self._setup_format_chooser()

    def _setup_format_chooser(self) -> None:
        """"""
        toggle_button = self.FormatChooser.get_first_child()
        toggle_button.add_css_class('flat')

        list_factory = Gtk.SignalListItemFactory()
        list_factory.connect('setup', self._setup_format_chooser_list_factory)
        list_factory.connect('bind', self._bind_format_chooser_list_factory)
        self.FormatChooser.set_list_factory(list_factory)

        factory_bytes = GLib.Bytes.new(self._get_format_chooser_factory_bytes())
        factory = Gtk.BuilderListItemFactory.new_from_bytes(None, factory_bytes)
        self.FormatChooser.set_factory(factory)

        def on_selected(*args) -> None:
            """"""
            value = self.FormatChooser.get_selected_item()
            value = value.get_string()
            key = next((k for k, v in FORMAT_OPTS.items() if v == value), 'csv')
            self._setup_main_container(key)

        self.FormatChooser.connect('notify::selected', on_selected)

        model = Gtk.StringList()
        for option in FORMAT_OPTS.values():
            model.append(option)
        self.FormatChooser.set_model(model)

    def _setup_format_chooser_list_factory(self,
                                           list_item_factory: Gtk.SignalListItemFactory,
                                           list_item:         Gtk.ListItem,
                                           ) ->               None:
        """"""
        box = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL,
                      hexpand     = True)
        list_item.set_child(box)

        label = Gtk.Label()
        box.append(label)

        image = Gtk.Image(icon_name = 'object-select-symbolic',
                          opacity   = 0.0)
        box.append(image)

        list_item.label = label
        list_item.image = image
        list_item.handler = None

    def _bind_format_chooser_list_factory(self,
                                          list_item_factory: Gtk.SignalListItemFactory,
                                          list_item:         Gtk.ListItem,
                                          ) ->               None:
        """"""
        item_data = list_item.get_item()
        label = item_data.get_string()

        list_item.label.set_label(label)

        def on_selected(*args) -> None:
            """"""
            is_selected = list_item.get_selected()
            list_item.image.set_opacity(is_selected)
            if is_selected:
                self.FormatChooser.set_tooltip_text(label)

        if list_item.handler:
            list_item.disconnect(list_item.handler)

        list_item.handler = self.FormatChooser.connect('notify::selected-item', on_selected)

        on_selected()

    def _get_format_chooser_factory_bytes(self) -> bytes:
        """"""
        return bytes(
            f"""
            <?xml version="1.0" encoding="UTF-8"?>
            <interface>
              <template class="GtkListItem">
                <property name="child">
                  <object class="GtkBox">
                    <property name="orientation">vertical</property>
                    <child>
                      <object class="GtkBox">
                        <property name="halign">center</property>
                        <property name="orientation">horizontal</property>
                        <child>
                          <object class="GtkLabel">
                            <property name="ellipsize">end</property>
                            <property name="label" translatable="yes">Format: </property>
                          </object>
                        </child>
                        <child>
                          <object class="GtkLabel">
                            <property name="ellipsize">end</property>
                            <binding name="label">
                              <lookup name="string" type="GtkStringObject">
                                <lookup name="item">GtkListItem</lookup>
                              </lookup>
                            </binding>
                          </object>
                        </child>
                      </object>
                    </child>
                    <child>
                      <object class="GtkLabel">
                        <property name="hexpand">true</property>
                        <property name="label">{self.subtitle}</property>
                        <style>
                          <class name="caption"/>
                          <class name="dimmed"/>
                          <class name="top-1px"/>
                        </style>
                      </object>
                    </child>
                  </object>
                </property>
              </template>
            </interface>
            """,
            'utf-8',
        )

    def _setup_main_container(self,
                              file_format: str,
                              ) ->         None:
        """"""
        match file_format:
            case 'csv':
                self.View = FileExportCSVView()
                self.MainContainer.set_child(self.View)

            case 'json':
                self.View = FileExportJSONView()
                self.MainContainer.set_child(self.View)

            case 'parquet':
                self.View = FileExportParquetView()
                self.MainContainer.set_child(self.View)

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
        return Gdk.EVENT_PROPAGATE

    @Gtk.Template.Callback()
    def _on_export_button_clicked(self,
                                  button: Gtk.Button,
                                  ) ->    None:
        """"""
        file_name = self.View.ExportAs.get_text()
        folder_path = self.View.ExportTo.get_text()
        file_path = f'{folder_path}/{file_name}.csv'

        from pathlib import Path
        file_path = str(Path(file_path).expanduser())

        if self._check_file_exists(file_path):
            return

        self.close()

        self._export_table()

    def _export_table(self) -> None:
        """"""
        if isinstance(self.View, FileExportCSVView):
            self._export_as_csv()

        if isinstance(self.View, FileExportJSONView):
            self._export_as_json()

        if isinstance(self.View, FileExportParquetView):
            self._export_as_parquet()

    def _check_file_exists(self,
                           file_path: str,
                           ) ->       bool:
        """"""
        file_path = Gio.File.new_for_path(file_path)

        if not file_path.query_exists(None):
            return False

        from os.path import basename
        file_basename = basename(file_path)

        alert_dialog = Adw.AlertDialog()

        alert_dialog.set_heading(_('Replace File?'))
        alert_dialog.set_body(_('A file named "{}" already exists. '
                                'Do you want to replace it?').format(file_basename))

        alert_dialog.add_response('cancel',  _('_Cancel'))
        alert_dialog.add_response('replace', _('_Replace'))

        alert_dialog.set_response_appearance('replace', Adw.ResponseAppearance.DESTRUCTIVE)
        alert_dialog.set_default_response('replace')
        alert_dialog.set_close_response('cancel')

        def on_dismissed(dialog: Adw.AlertDialog,
                         result: Gio.Task,
                         ) ->    None:
            """"""
            if result.had_error():
                return

            if dialog.choose_finish(result) != 'replace':
                return

            self.close()

            self._export_table()

        window = self.get_root()
        alert_dialog.choose(window, None, on_dismissed)

        return True

    def _export_as_csv(self) -> None:
        """"""
        file_name = self.View.ExportAs.get_text()
        folder_path = self.View.ExportTo.get_text()
        file_path = f'{folder_path}/{file_name}.csv'

        from pathlib import Path
        file_path = str(Path(file_path).expanduser())

        include_header  = self.View.IncludeHeader.get_active()

        separator       = self.View.Separator.get_text()
        line_terminator = self.View.LineTerminator.get_text()
        quote_char      = self.View.QuoteCharacter.get_text()

        datetime_format = self.View.DatetimeFormat.get_text()
        date_format     = self.View.DateFormat.get_text()
        time_format     = self.View.TimeFormat.get_text()

        # Escape special characters
        separator       = separator.encode().decode('unicode_escape')
        line_terminator = line_terminator.encode().decode('unicode_escape')
        quote_char      = quote_char.encode().decode('unicode_escape')

        # Convert empty string to None
        if datetime_format == '':
            datetime_format = None
        if date_format == '':
            date_format = None
        if time_format == '':
            time_format = None

        parameters = {
            'include_header':  include_header,
            'separator':       separator,
            'line_terminator': line_terminator,
            'quote_char':      quote_char,
            'datetime_format': datetime_format,
            'date_format':     date_format,
            'time_format':     time_format,
        }

        self.callback(file_path, parameters)

    def _export_as_json(self) -> None:
        """"""
        file_name = self.View.ExportAs.get_text()
        folder_path = self.View.ExportTo.get_text()
        file_path = f'{folder_path}/{file_name}.json'

        from pathlib import Path
        file_path = str(Path(file_path).expanduser())

        self.callback(file_path)

    def _export_as_parquet(self) -> None:
        """"""
        file_name = self.View.ExportAs.get_text()
        folder_path = self.View.ExportTo.get_text()
        file_path = f'{folder_path}/{file_name}.parquet'

        from pathlib import Path
        file_path = str(Path(file_path).expanduser())

        statistics        = self.View.Statistics.get_active()
        compression       = self.View.Compression.get_selected_item().get_string()
        compression_level = int(self.View.CompressionLevel.get_value())

        parameters = {
            'statistics':        statistics,
            'compression':       compression,
            'compression_level': compression_level,
        }

        self.callback(file_path, parameters)
