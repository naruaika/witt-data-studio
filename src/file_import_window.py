# file_import_window.py
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

from fastexcel import ExcelReader
from gi.repository import Adw
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Pango
from multiprocessing import Process
from multiprocessing import Queue
from polars import DataFrame

from .core.utils import get_file_format
from .core.file_manager import FileManager

COLUMNAR_FILES    = {'csv', 'tsv', 'txt', 'json', 'parquet'}
SPREADSHEET_FILES = {'xls', 'xlsx', 'xlsm', 'xlsb', 'xla', 'xlam', 'ods'}

def load_excel_file(excel_reader: ExcelReader,
                    output_queue: Queue,
                    n_rows:       int,
                    df_names:     list[str] = None,
                    ) ->          None:
    """"""
    dataframes = {}

    # Finally prior to v0.16.0, fastexcel releasing GIL when possible.
    # So we need to tweak this worker to load tables and sheets on a
    # different thread for each of them. Flag it as TODO. For more info,
    # see https://github.com/ToucanToco/fastexcel/releases/tag/v0.16.0.
    try:
        for table_name in excel_reader.table_names():
            if df_names is not None and table_name not in df_names:
                continue
            table = excel_reader.load_table(table_name, n_rows = n_rows)
            dataframes[table_name] = table.to_polars()
    except:
        pass # only XSLX files are supported for tables

    for sheet_name in excel_reader.sheet_names:
        if df_names is not None and sheet_name not in df_names:
            continue
        sheet = excel_reader.load_sheet(sheet_name, n_rows = n_rows)
        dataframes[sheet_name] = sheet.to_polars()

    return output_queue.put(dataframes)



@Gtk.Template(resource_path = '/com/wittara/studio/file_import_window.ui')
class FileImportWindow(Adw.Window):

    __gtype_name__ = 'FileImportWindow'

    WindowTitle      = Gtk.Template.Child()
    SplitView        = Gtk.Template.Child()
    Sidebar          = Gtk.Template.Child()

    SidebarHeaderBar = Gtk.Template.Child()
    ContentHeaderBar = Gtk.Template.Child()

    MainContainer    = Gtk.Template.Child()
    Spinner          = Gtk.Template.Child()
    StatusBox        = Gtk.Template.Child()
    BottomToolbar    = Gtk.Template.Child()
    ImportButton     = Gtk.Template.Child()

    PreferencesPage  = Gtk.Template.Child()
    FileSizeRow      = Gtk.Template.Child()
    LastModifiedRow  = Gtk.Template.Child()
    CreatedAtRow     = Gtk.Template.Child()

    DATA_SAMPLE_SIZE = 1_000

    def __init__(self,
                 file_path: str,
                 callback:  callable = None,
                 **kwargs:  dict,
                 ) ->       None:
        """"""
        from os.path import basename
        file_name = basename(file_path)
        kwargs['title'] = file_name

        super().__init__(**kwargs)

        self.file_path = file_path
        self.callback  = callback

        self.WindowTitle.set_title(file_name)

        self._setup_uinterfaces()
        self._setup_controllers()

    def _setup_uinterfaces(self) -> None:
        """"""
        self._setup_sidebar_toggler()

        self.u_kwargs = {}
        self.conf_widgets = {}

        self.file_format = get_file_format(self.file_path)
        self.file_format = self.file_format or 'csv'

        if self.file_format in COLUMNAR_FILES:
            self._setup_default_page()
            return

#       if self.file_format in SPREADSHEET_FILES:
#           self._setup_navigator_page()
#           return

        self._hide_spinner(fill_page = False)
        self._setup_error_page()

    def _setup_controllers(self) -> None:
        """"""
        controller = Gtk.EventControllerKey()
        controller.connect('key-pressed', self._on_key_pressed)
        self.add_controller(controller)

    def _setup_sidebar_toggler(self) -> None:
        """"""
        def on_sidebar_closed(button: Gtk.Button) -> None:
            """"""
            self.SplitView.set_show_sidebar(False)

        close_button = Gtk.Button(icon_name = 'go-previous-symbolic',
                                  visible   = False)
        close_button.connect('clicked', on_sidebar_closed)
        self.SidebarHeaderBar.pack_start(close_button)

        def on_sidebar_toggled(button: Gtk.ToggleButton) -> None:
            """"""
            toggled = button.get_active()
            self.SplitView.set_show_sidebar(toggled)

        visible = self.SplitView.get_collapsed() and \
                  not self.StatusBox.get_visible()
        active = self.SplitView.get_show_sidebar()
        toggle_button = Gtk.ToggleButton(icon_name = 'sidebar-show-symbolic',
                                         active    = active,
                                         visible   = visible)
        toggle_button.connect('toggled', on_sidebar_toggled)
        self.ContentHeaderBar.pack_start(toggle_button)

        def on_view_collapsed(split_view: Adw.OverlaySplitView,
                              param_spec: GObject.ParamSpec,
                              ) ->        None:
            """"""
            visible = self.SplitView.get_collapsed() and \
                      not self.StatusBox.get_visible()
            close_button.set_visible(visible)
            toggle_button.set_visible(visible)

        self.SplitView.connect('notify::collapsed', on_view_collapsed)

        def on_view_show_sidebar(split_view: Adw.OverlaySplitView,
                                 param_spec: GObject.ParamSpec,
                                 ) ->        None:
            """"""
            show_sidebar = split_view.get_show_sidebar()
            toggle_button.set_active(show_sidebar)

        self.SplitView.connect('notify::show-sidebar', on_view_show_sidebar)

    def _setup_error_page(self) -> None:
        """"""
        self.add_css_class('error')
        self.StatusBox.set_visible(True)

    def _setup_success_page(self) -> None:
        """"""
        subtitle = _('Showing up to 1,000 rows')
        self.WindowTitle.set_subtitle(subtitle)

        self.set_default_size(1280, 800)
        self.SplitView.set_collapsed(False)
        self.BottomToolbar.set_visible(True)

    def _setup_properties_box(self) -> None:
        """"""
        from os import stat
        from datetime import datetime

        file_stats = stat(self.file_path)
        file_size = file_stats.st_size
        file_size = file_size / 1024
        file_unit = 'KB'
        if file_size >= 1024:
            file_size = file_size / 1024
            file_unit = 'MB'
        if file_size >= 1024:
            file_size = file_size / 1024
            file_unit = 'GB'
        file_size = f'{file_size:.2f} {file_unit}'

        last_modified = datetime.fromtimestamp(file_stats.st_mtime)
        last_modified = last_modified.strftime('%d %B %Y %H:%M:%S')

        created_at = datetime.fromtimestamp(file_stats.st_ctime)
        created_at = created_at.strftime('%d %B %Y %H:%M:%S')

        self.FileSizeRow.set_subtitle(file_size)
        self.LastModifiedRow.set_subtitle(last_modified)
        self.CreatedAtRow.set_subtitle(created_at)

    def _hide_spinner(self,
                      fill_page: bool = True,
                      ) ->       None:
        """"""
        if fill_page:
            self.MainContainer.set_halign(Gtk.Align.FILL)
            self.MainContainer.set_valign(Gtk.Align.FILL)
        self.Spinner.set_visible(False)

    def _setup_data_viewer(self,
                           dataframe: DataFrame,
                           ) ->       None:
        """"""
        self.TopSeparator = Gtk.Separator(orientation = Gtk.Orientation.HORIZONTAL)
        self.MainContainer.append(self.TopSeparator)

        from .sheet.editor import SheetEditor
        tables = [((1, 1), dataframe)]
        configs = {'prefer-synchro': True,
                   'view-read-only': True}
        self.Editor = SheetEditor(tables  = tables,
                                  configs = configs)
        self.MainContainer.append(self.Editor)

        self.BottomSeparator = Gtk.Separator(orientation = Gtk.Orientation.HORIZONTAL)
        self.MainContainer.append(self.BottomSeparator)

        self.Editor.refresh_ui()
        self.Editor.grab_focus()

    def _get_current_settings(self,
                              read_only: bool = False,
                              ) ->       dict:
        """"""
        kwargs = {}

        match self.file_format:
            case 'csv' | 'tsv' | 'txt':
                from .file_import_csv_view import SEPARATOR_OPTS
                from .file_import_csv_view import QUOTE_CHAR_OPTS
                from .file_import_csv_view import DECIMAL_COMMA_OPTS

                kwargs['has_header']    = self.conf_widgets['has_header'].get_active()
                kwargs['skip_rows']     = int(self.conf_widgets['from_row'].get_value() - 1)
                kwargs['n_rows']        = int(self.conf_widgets['n_rows'].get_value()) or None
                kwargs['separator']     = self.conf_widgets['separator'].get_selected()
                kwargs['separator']     = list(SEPARATOR_OPTS.keys())[kwargs['separator']]
                kwargs['quote_char']    = self.conf_widgets['quote_char'].get_selected()
                kwargs['quote_char']    = list(QUOTE_CHAR_OPTS.keys())[kwargs['quote_char']]
                kwargs['decimal_comma'] = self.conf_widgets['decimal_comma'].get_selected()
                kwargs['decimal_comma'] = list(DECIMAL_COMMA_OPTS.keys())[kwargs['decimal_comma']]

                if not read_only:
                    kwargs['columns'] = self.conf_widgets['columns'].get_selected() or None

            case 'parquet':
                kwargs['n_rows'] = int(self.conf_widgets['n_rows'].get_value()) or None

                if not read_only:
                    kwargs['columns'] = self.conf_widgets['columns'].get_selected() or None

#           case _ if self.file_format in SPREADSHEET_FILES:
#               kwargs['df_names'] = self.conf_widgets['df_names'].get_selected() or None

        return kwargs

    @Gtk.Template.Callback()
    def _on_choose_file_button_clicked(self,
                                       button: Gtk.Button,
                                       ) ->    None:
        """"""
        self.close()

        window = self.get_transient_for()
        window.activate_action('app.open-file')

    @Gtk.Template.Callback()
    def _on_import_button_clicked(self,
                                  button: Gtk.Button,
                                  ) ->    None:
        """"""
        window = self.get_transient_for()

        self.close()
        window.present()

        all_columns = getattr(self, 'all_columns', [])
        kwargs = self._get_current_settings()

        if self.callback:
            self.callback(self.file_path, all_columns, **kwargs)
            return

        from .node.repository import NodeReadFile
        from .node.repository import NodeSheet
        from .node.repository import NodeViewer

        editor = window.node_editor

        canvas_width = editor.Canvas.get_width()
        canvas_height = editor.Canvas.get_height()
        viewport_width = window.TabView.get_width()
        viewport_height = window.TabView.get_height()

        window.history.grouping = True

        # Find the current active or create a new viewer node
        viewer = None
        for node in editor.nodes:
            if isinstance(node.parent, NodeViewer) and node.is_active():
                viewer = node
                break
        if not viewer:
            x_position = (canvas_width  - viewport_width)  / 2
            y_position = (canvas_height - viewport_height) / 2
            viewer = NodeViewer.new(x_position + (viewport_width  - 175) / 2 + 50,
                                    y_position + (viewport_height - 125) / 2)
            editor.add_node(viewer)
            editor.select_viewer(viewer)

        # Find a blank or create a new sheet node
        sheet = None
        for node in editor.nodes:
            if isinstance(node.parent, NodeSheet) and not node.has_data():
                sheet = node
                break
        if not sheet:
            target_position = (viewer.x - 175 - 50, viewer.y)
            sheet = NodeSheet.new(*target_position)
            editor.add_node(sheet)

        # Link the sheet to the viewer node if needed
        if not sheet.has_view():
            in_socket = sheet.contents[0].Socket
            out_socket = viewer.contents[-1].Socket
            editor.add_link(in_socket, out_socket)

        editor.auto_arrange(viewer)

        # Create a new reader node
        target_position = (sheet.x - 175 - 50, sheet.y)
        reader = NodeReadFile.new(*target_position)
        editor.add_node(reader)

        # Link the reader to the sheet node
        in_socket = reader.contents[0].Socket
        out_socket = sheet.contents[-1].Socket
        editor.add_link(in_socket, out_socket)

        window.activate_action('win.focus-editor')
        # TODO: go to the tab if reusing a sheet

        editor.select_by_click(reader)

        reader.set_data(self.file_path, all_columns, **kwargs)

        window.history.grouping = False

    #
    # Default UI
    #

    def _setup_default_page(self) -> None:
        """"""
        dataframe = FileManager.read_file(file_path   = self.file_path,
                                          sample_size = self.DATA_SAMPLE_SIZE,
                                          u_kwargs    = self.u_kwargs,
                                          eager_load  = True)

        if dataframe is None:
            self._setup_error_page()
            return

        self._setup_success_page()
        self._setup_properties_box()
        self._hide_spinner()

        self._setup_data_viewer(dataframe)
        self._setup_settings_box()

        self.ImportButton.grab_focus()

    def _setup_settings_box(self) -> None:
        """"""
        document = self.Editor.document
        main_table = document.tables[0]

        self.all_columns = main_table.columns

        match self.file_format:
            case 'csv' | 'tsv' | 'txt':
                from .file_import_csv_view import FileImportCsvView
                self.CustomView = FileImportCsvView(self.PreferencesPage,
                                                    self.u_kwargs,
                                                    self.conf_widgets,
                                                    main_table.columns,
                                                    self._refresh_default_page,
                                                    self._column_toggled)

            case 'parquet':
                from .file_import_parquet_view import FileImportParquetView
                self.CustomView = FileImportParquetView(self.PreferencesPage,
                                                        self.u_kwargs,
                                                        self.conf_widgets,
                                                        main_table.columns,
                                                        self._refresh_default_page,
                                                        self._column_toggled)

    def _refresh_default_page(self) -> None:
        """"""
        self._refresh_data_viewer(read_only = True)
        self._refresh_column_chooser()

    def _refresh_data_viewer(self,
                             dataframe: DataFrame = None,
                             read_only: bool      = False,
                             ) ->       None:
        """"""
        # I know this isn't efficient. But since we read a limited
        # number of rows only, I think that's not really a big issue.
        # Anyway, with this strategy, the user always get the latest
        # version of the file, so it'll be a huge benefit sometimes.
        if dataframe is None:
            kwargs = self._get_current_settings(read_only)
            dataframe = FileManager.read_file(file_path   = self.file_path,
                                              sample_size = self.DATA_SAMPLE_SIZE,
                                              u_kwargs    = self.u_kwargs,
                                              eager_load  = True,
                                              **kwargs)

        # I also know this is ugly, but it does the job
        # and I haven't found any glitches or whatever.
        self.TopSeparator.unparent()
        self.Editor.unparent()
        self.BottomSeparator.unparent()
        self._setup_data_viewer(dataframe)

    def _refresh_column_chooser(self) -> None:
        """"""
        if self.file_format not in {'csv', 'tsv', 'txt', 'parquet'}:
            return

        document = self.Editor.document
        main_table = document.tables[0]
        self.CustomView.update_columns(main_table.columns)

    def _column_toggled(self) -> None:
        """"""
        self._refresh_data_viewer(read_only = False)

    #
    # Navigator UI
    #

    def _setup_navigator_page(self) -> None:
        """"""
        try:
            reader = FileManager.read_file(self.file_path)
        except Exception:
            self._setup_error_page()
            return

        self.dataframes: dict = {}

        self._setup_success_page()
        self._setup_properties_box()

        data_queue = Queue()
        loading_process = Process(target = load_excel_file,
                                  args   = (reader,
                                            data_queue,
                                            self.DATA_SAMPLE_SIZE),
                                  daemon = False)
        loading_process.start()

        def check_data_queue() -> bool:
            """"""
            if not data_queue.empty():
                self.dataframes = data_queue.get()
                first_key = list(self.dataframes.keys())[0]
                dataframe = self.dataframes[first_key]

                self._setup_navigation_box()
                self._setup_data_viewer(dataframe)
                self._hide_spinner()

                self.Sidebar.set_sensitive(True)
                self.ImportButton.set_sensitive(True)

                loading_process.join()
                return False
            return True

        GLib.idle_add(check_data_queue)
        self.Sidebar.set_sensitive(False)
        self.ImportButton.set_sensitive(False)

    def _setup_navigation_box(self) -> None:
        """"""
        group = Adw.PreferencesGroup(title = _('Which Data to Pick?'))
        self.PreferencesPage.add(group)

        row = Adw.PreferencesRow()
        row.set_activatable(False)
        group.add(row)

        self.NavigationFlowBox = Gtk.FlowBox(selection_mode        = Gtk.SelectionMode.NONE,
                                             homogeneous           = True,
                                             min_children_per_line = 2,
                                             margin_top            = 6,
                                             margin_bottom         = 6,
                                             margin_start          = 4,
                                             margin_end            = 4,
                                             column_spacing        = 4,
                                             row_spacing           = 4)
        self.NavigationFlowBox.add_css_class('navigation-sidebar')
        row.set_child(self.NavigationFlowBox)

        df_names = list(self.dataframes.keys())
        self.NavigationFlowBox.selected = df_names
        self.NavigationFlowBox.nactive = df_names[0]

        def get_selected() -> list[str]:
            """"""
            return self.NavigationFlowBox.selected
        self.NavigationFlowBox.get_selected = get_selected

        self._populate_navigation_flow_box()

        self.conf_widgets['df_names'] = self.NavigationFlowBox

    def _populate_navigation_flow_box(self,
                                      checked: bool = True,
                                      ) ->     None:
        """"""
        def _show_related_dataframe(button:  Gtk.Button,
                                    df_name: str,
                                    ) ->     None:
            """"""
            if self.NavigationFlowBox.nactive == df_name:
                return

            box = button.get_parent()
            flow_box_child = box.get_parent()
            flow_box_child.add_css_class('active-item')

            self.NavigationFlowBox.wactive.remove_css_class('active-item')
            self.NavigationFlowBox.wactive = flow_box_child
            self.NavigationFlowBox.nactive = df_name

            dataframe = self.dataframes[df_name]
            self._refresh_data_viewer(dataframe)

        def on_check_toggled(button:  Gtk.CheckButton,
                             df_name: str,
                             is_meta: bool = False,
                             ) ->     None:
            """"""
            if is_meta:
                checked = button.get_active()
                self._populate_navigation_flow_box(checked)
                return

            selected = self.NavigationFlowBox.selected
            selected.append(df_name) if button.get_active() \
                                     else selected.remove(df_name)
            self.NavigationFlowBox.selected = selected

            _show_related_dataframe(button, df_name)

        def on_view_button_clicked(button:  Gtk.Button,
                                   df_name: str,
                                   ) ->     None:
            """"""
            _show_related_dataframe(button, df_name)

        self.NavigationFlowBox.remove_all()

        df_names = list(self.dataframes.keys())
        df_names = [_('Select All')] + df_names

        for df_idx, df_name in enumerate(df_names):
            is_meta = df_idx == 0

            box = Gtk.Box(hexpand = True)
            box.add_css_class('linked')
            self.NavigationFlowBox.append(box)

            label = Gtk.Label(halign       = Gtk.Align.START,
                              valign       = Gtk.Align.CENTER,
                              hexpand      = True,
                              ellipsize    = Pango.EllipsizeMode.END,
                              label        = df_name,
                              tooltip_text = df_name)

            check_button = Gtk.CheckButton(active        = checked,
                                           hexpand       = True,
                                           margin_top    = 2,
                                           margin_bottom = 2,
                                           margin_start  = 2,
                                           margin_end    = 2)
            check_button.connect('toggled', on_check_toggled, df_name, is_meta)
            check_button.set_child(label)
            box.append(check_button)

            if not is_meta:
                view_button = Gtk.Button(icon_name = 'go-next-symbolic')
                view_button.add_css_class('arrow-right')
                view_button.add_css_class('flat')
                view_button.connect('clicked', on_view_button_clicked, df_name)
                box.append(view_button)

            if self.NavigationFlowBox.nactive == df_name:
                flow_box_child = box.get_parent()
                flow_box_child.add_css_class('active-item')
                self.NavigationFlowBox.wactive = flow_box_child

        self.NavigationFlowBox.selected = df_names if checked else []

    def _on_key_pressed(self,
                        event:   Gtk.EventControllerKey,
                        keyval:  int,
                        keycode: int,
                        state:   Gdk.ModifierType,
                        ) ->     bool:
        """"""
#       if keyval == Gdk.KEY_Escape:
#           self.close()
#           return Gdk.EVENT_STOP
        return Gdk.EVENT_PROPAGATE
