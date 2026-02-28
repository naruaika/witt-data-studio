# database_import_window.py
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

from copy import deepcopy
from gi.repository import Adw
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import GtkSource
from gi.repository import Pango
from keyring import delete_password
from keyring import get_password
from keyring import set_password
from polars import DataFrame
import gc

from .core.utils import generate_uuid

class ConnectionListItem(GObject.Object):

    __gtype_name__ = 'ConnectionListItem'

    dialect = GObject.Property(type = str, default = '')
    cname   = GObject.Property(type = str, default = '')
    uuid    = GObject.Property(type = str, default = '')

    def __init__(self,
                 dialect: str,
                 cname:   str,
                 uuid:    str,
                 config:  dict,
                 ) ->     None:
        """"""
        super().__init__()

        self.dialect = dialect
        self.cname   = cname
        self.uuid    = uuid
        self.config  = config


@Gtk.Template(resource_path = '/com/wittara/studio/database_import_window.ui')
class DatabaseImportWindow(Adw.Window):

    __gtype_name__ = 'DatabaseImportWindow'

    SplitView        = Gtk.Template.Child()

    SidebarHeaderBar = Gtk.Template.Child()
    ContentHeaderBar = Gtk.Template.Child()

    SearchEntry      = Gtk.Template.Child()
    ConnectionMenu   = Gtk.Template.Child()

    ListViewBox      = Gtk.Template.Child()
    ListView         = Gtk.Template.Child()
    Selection        = Gtk.Template.Child()
    ListStatusPage   = Gtk.Template.Child()

    ViewStack        = Gtk.Template.Child()
    SourceView       = Gtk.Template.Child()
    OutputStatusPage = Gtk.Template.Child()
    OutputViewBox    = Gtk.Template.Child()
    OutputView       = Gtk.Template.Child()
    LogsStatusPage   = Gtk.Template.Child()
    LogsViewBox      = Gtk.Template.Child()
    LogsView         = Gtk.Template.Child()

    ContextLabelBox  = Gtk.Template.Child()
    ContextLabel     = Gtk.Template.Child()
    RunButton        = Gtk.Template.Child()
    RunSpinner       = Gtk.Template.Child()
    ImportButton     = Gtk.Template.Child()

    APPLICATION_ID = 'com.wittara.studio'

    def __init__(self,
                 query:    str      = None,
                 config:   dict     = None,
                 callback: callable = None,
                 **kwargs: dict,
                 ) ->      None:
        """"""
        super().__init__(**kwargs)

        if config:
            keys = {'dialect', 'host', 'port', 'database', 'username'}
            config = deepcopy(config)
            config = {k: v for k, v in config.items() if k in keys}

        self.query    = query
        self.config   = config
        self.callback = callback

        self.connection_list = []

        self._last_exec_item = None

        self._setup_uinterfaces()
        self._setup_actions()
        self._setup_controllers()

        self._restore_connection_list()
        self._populate_connection_list_view()

    def _setup_uinterfaces(self) -> None:
        """"""
        self._setup_sidebar_toggle_button()
        self._setup_filter_toggle_button()
        self._setup_new_connection_button()
        self._setup_connection_list_view()
        self._setup_connection_selection()
        self._setup_primary_view_stack()
        self._setup_query_source_view()
        self._setup_logs_text_view()

    def _setup_sidebar_toggle_button(self) -> None:
        """"""
        close_button = Gtk.Button(icon_name = 'go-previous-symbolic',
                                  visible   = False)
        self.SidebarHeaderBar.pack_start(close_button)

        def on_sidebar_closed(button: Gtk.Button) -> None:
            """"""
            self.SplitView.set_show_sidebar(False)

        close_button.connect('clicked', on_sidebar_closed)

        visible = self.SplitView.get_collapsed()
        active = self.SplitView.get_show_sidebar()
        toggle_button = Gtk.ToggleButton(icon_name = 'sidebar-show-symbolic',
                                         active    = active,
                                         visible   = visible)
        self.ContentHeaderBar.pack_start(toggle_button)

        def on_sidebar_toggled(button: Gtk.ToggleButton) -> None:
            """"""
            toggled = button.get_active()
            self.SplitView.set_show_sidebar(toggled)

        toggle_button.connect('toggled', on_sidebar_toggled)

        def on_view_collapsed(split_view: Adw.OverlaySplitView,
                              param_spec: GObject.ParamSpec,
                              ) ->        None:
            """"""
            visible = self.SplitView.get_collapsed()
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

    def _setup_filter_toggle_button(self) -> None:
        """"""
        button = Gtk.ToggleButton(icon_name    = 'edit-find-symbolic',
                                  tooltip_text = _('Filter Connection'))
        self.SidebarHeaderBar.pack_start(button)

        def on_toggled(button: Gtk.ToggleButton) -> None:
            """"""
            active = button.get_active()
            self.SearchEntry.set_visible(active)
            if active:
                self.SearchEntry.grab_focus()

        button.connect('toggled', on_toggled)

    def _setup_new_connection_button(self) -> None:
        """"""
        button = Gtk.MenuButton(icon_name    = 'list-add-symbolic',
                                tooltip_text = _('New Connection'),
                                menu_model   = self.ConnectionMenu)
        self.SidebarHeaderBar.pack_end(button)

    def _setup_connection_list_view(self) -> None:
        """"""
        self.ListStore = Gio.ListStore.new(ConnectionListItem)
        self.Selection.set_model(self.ListStore)

        factory = Gtk.SignalListItemFactory()
        factory.connect('setup', self._setup_connection_list_factory)
        factory.connect('bind', self._bind_connection_list_factory)
        factory.connect('unbind', self._unbind_connection_list_factory)
        self.ListView.set_factory(factory)

    def _setup_connection_selection(self) -> None:
        """"""
        def on_selected(*args) -> None:
            """"""
            item = self.Selection.get_selected_item()

            if not item:
                self.ContextLabelBox.set_visible(False)
                self.RunButton.set_sensitive(False)
                self.ImportButton.set_sensitive(False)
                return

            self.ContextLabel.set_label(item.cname)
            self.ContextLabelBox.set_visible(True)
            self.RunButton.set_sensitive(True)
            self.ImportButton.set_sensitive(True)

            if self.SplitView.get_collapsed():
                self.SplitView.set_show_sidebar(False)

            self.ViewStack.set_visible_child_name('query')
            self.SourceView.grab_focus()

        self.Selection.connect('notify::selected', on_selected)

    def _setup_connection_list_factory(self,
                                       list_item_factory: Gtk.SignalListItemFactory,
                                       list_item:         Gtk.ListItem,
                                       ) ->               None:
        """"""
        root_box = Gtk.Box()
        list_item.set_child(root_box)

        parent_box = Gtk.CenterBox(orientation   = Gtk.Orientation.HORIZONTAL,
                                   hexpand       = True,
                                   margin_top    = 12,
                                   margin_bottom = 12,
                                   margin_start  = 6,
                                   margin_end    = 6)
        root_box.append(parent_box)

        start_box = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL,
                            valign      = Gtk.Align.CENTER,
                            hexpand     = True,
                            spacing     = 8)
        parent_box.set_start_widget(start_box)

        icon = Gtk.Image(icon_name = 'network-server-symbolic',
                         valign    = Gtk.Align.CENTER)
        icon.add_css_class('dimmed')
        start_box.append(icon)

        cname = Gtk.Label(halign    = Gtk.Align.START,
                          hexpand   = True,
                          ellipsize = Pango.EllipsizeMode.END)
        start_box.append(cname)

        dialect = Gtk.Label(halign = Gtk.Align.START)
        dialect.add_css_class('dimmed')
        parent_box.set_end_widget(dialect)

        def on_rmb_click(gesture: Gtk.GestureClick,
                         n_press: int,
                         x:       float,
                         y:       float,
                         ) ->     None:
            """"""
            item_data = list_item.get_item()

            menu = Gio.Menu.new()
            menu.append(_('_Copy'),      f"app.copy-string('{item_data.cname}')")
            menu.append(_('_Rename...'), f"connection.rename('{item_data.uuid}')")
            menu.append(_('_Edit...'),   f"connection.edit('{item_data.uuid}')")
            menu.append(_('_Delete'),    f"connection.delete('{item_data.uuid}')")

            rect = Gdk.Rectangle()
            rect.x = x
            rect.y = y
            rect.width  = 1
            rect.height = 1

            popover = Gtk.PopoverMenu(has_arrow   = False,
                                      pointing_to = rect,
                                      menu_model  = menu)
            popover.set_parent(root_box)
            popover.popup()

            parent_box = root_box.get_parent()
            parent_box.add_css_class('has-open-popup')

            def on_closed(popover: Gtk.PopoverMenu) -> None:
                """"""
                parent_box.remove_css_class('has-open-popup')
                GLib.timeout_add(1000, popover.unparent)

            popover.connect('closed', on_closed)

        controller = Gtk.GestureClick(button = Gdk.BUTTON_SECONDARY)
        controller.connect('pressed', on_rmb_click)
        root_box.add_controller(controller)

        list_item.cname   = cname
        list_item.dialect = dialect
        list_item.clabel  = None

    def _bind_connection_list_factory(self,
                                      list_item_factory: Gtk.SignalListItemFactory,
                                      list_item:         Gtk.ListItem,
                                      ) ->               None:
        """"""
        item_data = list_item.get_item()

        list_item.cname.set_label(item_data.cname)

        dialects = {
            'mysql':      'MySQL',
            'postgresql': 'PostgreSQL',
            'sqlite':     'SQLite',
            'duckdb':     'DuckDB',
        }
        dialect = item_data.dialect
        dialect = dialects.get(dialect, dialect)
        list_item.dialect.set_label(dialect)

        list_item.clabel = item_data.bind_property('cname', list_item.cname, 'label')

    def _unbind_connection_list_factory(self,
                                        list_item_factory: Gtk.SignalListItemFactory,
                                        list_item:         Gtk.ListItem,
                                        ) ->               None:
        """"""
        list_item.clabel.unbind()

    def _setup_primary_view_stack(self) -> None:
        """"""
        def on_page_changed(*args) -> None:
            """"""
            page_name = self.ViewStack.get_visible_child_name()
            match page_name:
                case 'query':
                    self.SourceView.grab_focus()
                case 'output':
                    if self.OutputViewBox.get_visible():
                        editor = self.OutputView.get_child()
                        editor.grab_focus()
                case 'logs':
                    if self.LogsViewBox.get_visible():
                        self.LogsView.grab_focus()

        self.ViewStack.connect('notify::visible-child', on_page_changed)

    def _setup_query_source_view(self) -> None:
        """"""
        language_manager = GtkSource.LanguageManager.get_default()
        language = language_manager.get_language('sql')

        self.SourceBuffer = GtkSource.Buffer(language         = language,
                                             highlight_syntax = True,
                                             text             = self.query or '')
        self.SourceView.set_buffer(self.SourceBuffer)

        def auto_scroll_to_cursor(adjustment: Gtk.Adjustment) -> None:
            """"""
            buffer = self.SourceView.get_buffer()
            cursor_mark = buffer.get_insert()
            cursor_iter = buffer.get_iter_at_mark(cursor_mark)
            self.SourceView.scroll_to_iter(cursor_iter, 0, False, 0, 0)

        scrolled_window = self.SourceView.get_parent()
        vadjustment = scrolled_window.get_vadjustment()
        vadjustment.connect('changed', auto_scroll_to_cursor)

        settings = Gtk.Settings.get_default()
        settings.connect('notify::gtk-application-prefer-dark-theme',
                         self._on_prefer_dark_theme_changed)

        self._on_prefer_dark_theme_changed(None, None)

    def _setup_logs_text_view(self) -> None:
        """"""
        def auto_scroll_to_cursor(adjustment: Gtk.Adjustment) -> None:
            """"""
            buffer = self.LogsView.get_buffer()
            cursor_mark = buffer.get_insert()
            cursor_iter = buffer.get_iter_at_mark(cursor_mark)
            self.LogsView.scroll_to_iter(cursor_iter, 0, False, 0, 0)

        scrolled_window = self.LogsView.get_parent()
        vadjustment = scrolled_window.get_vadjustment()
        vadjustment.connect('changed', auto_scroll_to_cursor)

    def _on_prefer_dark_theme_changed(self,
                                      settings:     Gtk.Settings,
                                      gparamstring: str,
                                      ) ->          None:
        """"""
        scheme_manager = GtkSource.StyleSchemeManager.get_default()
        prefers_dark = Adw.StyleManager().get_dark()
        color_scheme = 'Adwaita-dark' if prefers_dark else 'Adwaita'
        style_scheme = scheme_manager.get_scheme(color_scheme)
        self.SourceBuffer.set_style_scheme(style_scheme)

    def _setup_actions(self) -> None:
        """"""
        group = Gio.SimpleActionGroup.new()
        self.insert_action_group('connection', group)

        controller = Gtk.ShortcutController()
        self.add_controller(controller)

        def create_action(name:       str,
                          callback:   callable,
                          shortcuts:  list[str]        = [],
                          param_type: GLib.VariantType = None,
                          ) ->        None:
            """"""
            action = Gio.SimpleAction.new(name, param_type)
            action.connect('activate', callback)
            group.add_action(action)

            if shortcuts:
                trigger = Gtk.ShortcutTrigger.parse_string('|'.join(shortcuts))
                string_action = f'action(connection.{name})'
                action = Gtk.ShortcutAction.parse_string(string_action)
                shortcut = Gtk.Shortcut.new(trigger, action)
                controller.add_shortcut(shortcut)

        create_action('add-new',   callback   = self._on_add_new_action,
                                   param_type = GLib.VariantType('s'))
        create_action('rename',    callback   = self._on_rename_action,
                                   param_type = GLib.VariantType('s'))
        create_action('edit',      callback   = self._on_edit_action,
                                   param_type = GLib.VariantType('s'))
        create_action('delete',    callback   = self._on_delete_action,
                                   param_type = GLib.VariantType('s'))

        create_action('run-all',   lambda *_: self._run_query(block_only = False),
                                   ['F5'])
        create_action('run-block', lambda *_: self._run_query(block_only = True),
                                   ['<Shift>F5'])

    def _on_add_new_action(self,
                           action:    Gio.SimpleAction,
                           parameter: GLib.Variant,
                           ) ->       None:
        """"""
        dialect = parameter.get_string()

        def do_add(config: dict) -> None:
            """"""
            config = deepcopy(config)
            config['dialect'] = dialect

            # Save password into system keyring
            password = config.get('password')
            if password is not None:
                from .core.connection_manager import ConnectionManager
                username = ConnectionManager.hash_config(config)
                set_password(self.APPLICATION_ID, username, password)

            if 'password' in config:
                del config['password']

            from .core.utils import generate_uuid
            config['uuid'] = generate_uuid()

            self.connection_list.append(config)

            list_item = ConnectionListItem(config['dialect'],
                                           config['alias'],
                                           config['uuid'],
                                           config)
            self.ListStore.append(list_item)

            self.ListStatusPage.set_visible(False)
            self.ListViewBox.set_visible(True)

            self._save_connection_list()

        application = self.get_application()

        from .database_add_window import DatabaseAddWindow
        add_window = DatabaseAddWindow(dialect       = dialect,
                                       callback      = do_add,
                                       transient_for = self,
                                       application   = application)
        add_window.present()

    def _on_rename_action(self,
                          action:    Gio.SimpleAction,
                          parameter: GLib.Variant,
                          ) ->       None:
        """"""
        uuid = parameter.get_string()

        cname = next((c['alias'] for c in self.connection_list if c['uuid'] == uuid), '')

        dialog = Adw.AlertDialog(heading = _('Rename Connection'))

        dialog.add_response('cancel', _('_Cancel'))
        dialog.add_response('rename', _('_Rename'))

        dialog.set_response_appearance('rename', Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response('rename')
        dialog.set_close_response('cancel')

        entry = Adw.EntryRow(title = _('Name'),
                             text  = cname)
        entry.add_css_class('card')
        dialog.set_extra_child(entry)

        def on_dismissed(dialog: Adw.AlertDialog,
                         result: Gio.Task,
                         ) ->    None:
            """"""
            if result.had_error():
                return
            if dialog.choose_finish(result) == 'cancel':
                return

            new_name = entry.get_text()

            for index in range(self.ListStore.get_n_items()):
                item = self.ListStore.get_item(index)
                if item.uuid == uuid:
                    item.cname = new_name
                    connection = self.connection_list[index]
                    connection['alias'] = new_name
                    break

            model = self.Selection.get_model()
            for index in range(model.get_n_items()):
                item = model.get_item(index)
                if item.uuid == uuid:
                    item.cname = new_name
                    break

            self._save_connection_list()

            dialog.close()

        dialog.choose(self, None, on_dismissed)

        entry.grab_focus()

    def _on_edit_action(self,
                        action:    Gio.SimpleAction,
                        parameter: GLib.Variant,
                        ) ->       None:
        """"""
        from .core.connection_manager import ConnectionManager

        uuid = parameter.get_string()

        for config in self.connection_list:
            if config['uuid'] == uuid:
                dialect = config['dialect']
                break

        def do_edit(new_config: dict) -> None:
            """"""
            new_config = deepcopy(new_config)
            new_config['dialect'] = dialect

            # Update password in system keyring
            password = new_config.get('password')
            if password is not None:
                username = ConnectionManager.hash_config(config)
                if get_password(self.APPLICATION_ID, username):
                    delete_password(self.APPLICATION_ID, username)

                username = ConnectionManager.hash_config(new_config)
                set_password(self.APPLICATION_ID, username, password)

            if 'password' in new_config:
                del new_config['password']

            new_config['uuid'] = config['uuid']

            for index in range(self.ListStore.get_n_items()):
                item = self.ListStore.get_item(index)
                if item.uuid == uuid:
                    item.cname = new_config['alias']
                    item.config = new_config
                    self.connection_list[index] = new_config
                    break

            model = self.Selection.get_model()
            for index in range(model.get_n_items()):
                item = model.get_item(index)
                if item.uuid == uuid:
                    item.cname = new_config['alias']
                    item.config = new_config
                    break

            self._save_connection_list()

        application = self.get_application()

        from .database_add_window import DatabaseAddWindow
        add_window = DatabaseAddWindow(dialect       = dialect,
                                       callback      = do_edit,
                                       transient_for = self,
                                       application   = application)

        add_window.set_data(config)

        if config.get('host'):
            username = ConnectionManager.hash_config(config)
            password = get_password(self.APPLICATION_ID, username)
            if password is not None:
                add_window.set_password(password)

        add_window.present()

    def _on_delete_action(self,
                          action:    Gio.SimpleAction,
                          parameter: GLib.Variant,
                          ) ->       None:
        """"""
        uuid = parameter.get_string()

        cname = next((c['alias'] for c in self.connection_list if c['uuid'] == uuid), '')

        heading = _('Delete Connection?')
        label = f"<span weight='bold'>\"{cname}\"</span>"
        body = _("Are you sure to delete {}? "
                 "This action cannot be undone.".format(label))

        dialog = Adw.AlertDialog(heading         = heading,
                                 body            = body,
                                 body_use_markup = True)

        dialog.add_response('cancel', _('_Cancel'))
        dialog.add_response('delete', _('_Delete'))

        dialog.set_response_appearance('delete', Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response('delete')
        dialog.set_close_response('cancel')

        def on_dismissed(dialog: Adw.AlertDialog,
                         result: Gio.Task,
                         ) ->    None:
            """"""
            if result.had_error():
                return
            if dialog.choose_finish(result) == 'cancel':
                return

            for index in range(self.ListStore.get_n_items()):
                item = self.ListStore.get_item(index)
                if item.uuid == uuid:
                    self.ListStore.remove(index)
                    del self.connection_list[index]
                    break

            model = self.Selection.get_model()
            for index in range(model.get_n_items()):
                item = model.get_item(index)
                if item.uuid == uuid:
                    model.remove(index)
                    break

            self._save_connection_list()

            dialog.close()

        dialog.choose(self, None, on_dismissed)

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
        if state & Gdk.ModifierType.ALT_MASK:
            if keyval == Gdk.KEY_1:
                self.ViewStack.set_visible_child_name('query')
                return Gdk.EVENT_STOP
            if keyval == Gdk.KEY_2:
                self.ViewStack.set_visible_child_name('output')
                return Gdk.EVENT_STOP
            if keyval == Gdk.KEY_3:
                self.ViewStack.set_visible_child_name('logs')
                return Gdk.EVENT_STOP

        if state & Gdk.ModifierType.CONTROL_MASK and \
                keyval == Gdk.KEY_Escape:
            self.close()
            return Gdk.EVENT_STOP

        return Gdk.EVENT_PROPAGATE

    def _restore_connection_list(self) -> None:
        """"""
        from json import loads
        settings = Gio.Settings.new(self.APPLICATION_ID)
        list_str = settings.get_string('connection-list')
        list_obj = loads(list_str)

        for index in range(len(list_obj)):
            list_obj[index]['uuid'] = generate_uuid()

        self.connection_list += list_obj

    def _save_connection_list(self) -> None:
        """"""
        from json import dumps
        list_obj = deepcopy(self.connection_list)
        list_str = dumps(list_obj)
        settings = Gio.Settings.new(self.APPLICATION_ID)
        settings.set_string('connection-list', list_str)

    def _populate_connection_list_view(self) -> None:
        """"""
        self.ListStore.remove_all()

        selected = Gtk.INVALID_LIST_POSITION

        for index, config in enumerate(self.connection_list):
            list_item = ConnectionListItem(config['dialect'],
                                           config['alias'],
                                           config['uuid'],
                                           config)
            self.ListStore.append(list_item)

            config = deepcopy(config)
            del config['alias']
            del config['uuid']

            if config == self.config:
                selected = index

        else:
            self.ListStatusPage.set_visible(False)
            self.ListViewBox.set_visible(True)

            if selected == Gtk.INVALID_LIST_POSITION:
                if self.config:
                    list_item = ConnectionListItem(self.config.get('dialect'),
                                                   _('Unsaved Connection'),
                                                   generate_uuid(),
                                                   self.config)
                    self.ListStore.append(list_item)
                    self.Selection.set_selected(index + 1)
                else:
                    self.Selection.set_selected(0)
            else:
                self.Selection.set_selected(selected)

    def _get_active_query_block(self) -> str:
        """"""
        buffer = self.SourceView.get_buffer()

        # Only get text within the selection bounds
        if buffer.get_has_selection():
            start_iter, end_iter = buffer.get_selection_bounds()
            text = buffer.get_text(start_iter, end_iter, True)

        # Find text block from the cursor position
        else:
            cursor_mark = buffer.get_insert()
            cursor_iter = buffer.get_iter_at_mark(cursor_mark)

            line_count = buffer.get_line_count()
            line_number = cursor_iter.get_line()

            _, start_iter = buffer.get_iter_at_line(line_number)
            end_iter = start_iter.copy()
            end_iter.forward_line()

            _text = buffer.get_text(start_iter, end_iter, True)
            if _text.strip() == '':
                return ''

            # Find query block start
            _start_iter = start_iter.copy()
            while _start_iter.get_line() > 0:
                _end_iter = _start_iter.copy()
                _start_iter.backward_line()
                _text = buffer.get_text(_start_iter, _end_iter, True)
                if _text.strip() == '' or _start_iter.get_line() == 0:
                    if _start_iter.get_line() > 0:
                        _start_iter.forward_line()
                    start_iter = _start_iter.copy()
                    break

            # Find query block end
            _end_iter = start_iter.copy()
            while _end_iter.get_line() < line_count:
                _start_iter = _end_iter.copy()
                _end_iter.forward_line()
                _text = buffer.get_text(_start_iter, _end_iter, True)
                if _text.strip() == '':
                    if _start_iter.get_line() < _end_iter.get_line():
                        _end_iter.backward_line()
                    end_iter = _end_iter.copy()
                    break

            text = buffer.get_text(start_iter, end_iter, True)
            text = text.strip()

            GLib.idle_add(buffer.select_range, start_iter, end_iter)

        return text

    def _run_query(self,
                   block_only: bool = True,
                   ) ->        None:
        """"""
        citem = self.Selection.get_selected_item()

        if not citem:
            return

        if not block_only:
            buffer = self.SourceView.get_buffer()
            start_iter = buffer.get_start_iter()
            end_iter = buffer.get_end_iter()
            query = buffer.get_text(start_iter, end_iter, True)
            query = query.strip()
        else:
            query = self._get_active_query_block()

        if not query:
            return

        def do_run() -> None:
            """"""
            from .core.connection_manager import ConnectionManager

            config = deepcopy(citem.config)

            # Get password from system keyring
            if config.get('host'):
                username = ConnectionManager.hash_config(config)
                password = get_password(self.APPLICATION_ID, username)
                config['password'] = password

            output, log_info = ConnectionManager.execute(dialect   = citem.dialect,
                                                         config    = config,
                                                         query     = query,
                                                         n_samples = 1_000)

            # Hide password from log message
            if (password := config.get('password')) and (message := log_info['message']):
                log_info['message'] = message.replace(password, '*' * len(password))

            # Show query execution output
            if isinstance(output, DataFrame):
                GLib.idle_add(self._refresh_table_output_view, output)
                GLib.idle_add(self.ViewStack.set_visible_child_name, 'output')
                GLib.idle_add(self._update_execution_logs_view, log_info)
            else:
                GLib.idle_add(self.ViewStack.set_visible_child_name, 'logs')
                GLib.idle_add(self._update_execution_logs_view, log_info)

            GLib.idle_add(self.RunSpinner.set_visible, False)
            GLib.idle_add(self.RunButton.set_sensitive, True)

        self.RunSpinner.set_visible(True)
        self.RunButton.set_sensitive(False)

        from threading import Thread
        Thread(target = do_run, daemon = True).start()

    def _refresh_table_output_view(self,
                                   dataframe: DataFrame,
                                   ) ->       None:
        """"""
        from .sheet.editor import SheetEditor
        tables = {_('Table'): ((1, 1), dataframe)} \
                 if dataframe is not None else {}
        configs = {'prefer-synchro': True,
                   'view-read-only': True}
        editor = SheetEditor(tables  = tables,
                             configs = configs)
        self.OutputView.set_child(editor)

        self.OutputStatusPage.set_visible(False)
        self.OutputViewBox.set_visible(True)

        editor.refresh_ui()

        gc.collect()

    def _update_execution_logs_view(self,
                                    log_info: str,
                                    ) ->      None:
        """"""
        from datetime import datetime

        new_log = log_info['query']

        if message := log_info['message']:
            new_log += f'\n\n{message}'

        duration = log_info['duration']
        executed = log_info['executed']
        executed = datetime.fromtimestamp(executed)
        executed = executed.strftime(f"{_('on')} %Y-%m-%d "
                                     f"{_('at')} %H:%M:%S")

        new_log += f'\n\n>>> {_('Completed in')} {duration:.4f}s {executed}'

        buffer = self.LogsView.get_buffer()
        start_iter = buffer.get_start_iter()
        end_iter = buffer.get_end_iter()

        logs = buffer.get_text(start_iter, end_iter, True)

        if logs != '':
            logs += '\n\n'
        logs += new_log

        buffer.set_text(logs)

        self.LogsStatusPage.set_visible(False)
        self.LogsViewBox.set_visible(True)

    @Gtk.Template.Callback()
    def _on_search_entry_changed(self,
                                 entry: Gtk.Entry,
                                 ) ->    None:
        """"""
        def auto_select() -> None:
            """"""
            model = self.Selection.get_model()
            if model.get_n_items() == 0:
                return
            if not self.Selection.get_selected_item():
                self.Selection.set_selected(0)

        n_items = self.ListStore.get_n_items()

        if n_items == 0:
            return

        query = entry.get_text()

        if query == '':
            self.Selection.set_model(self.ListStore)
            auto_select()
            return

        new_list_store = Gio.ListStore()

        for iidx in range(n_items):
            item = self.ListStore.get_item(iidx)
            if query in item.cname:
                new_list_store.append(item)

        self.Selection.set_model(new_list_store)

        auto_select()

    @Gtk.Template.Callback()
    def _on_import_button_clicked(self,
                                  button: Gtk.Button,
                                  ) ->    None:
        """"""
        item = self.Selection.get_selected_item()

        if not item:
            return

        window = self.get_transient_for()

        self.close()
        window.present()

        config = deepcopy(item.config)

        if 'uuid' in config:
            del config['uuid']
        if 'password' in config:
            del config['password']

        buffer = self.SourceView.get_buffer()
        start_iter = buffer.get_start_iter()
        end_iter = buffer.get_end_iter()
        query = buffer.get_text(start_iter, end_iter, True)
        query = query.strip()

        if self.callback:
            self.callback(query, config)
            return

        from .node.repository import NodeReadDatabase
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
        reader = NodeReadDatabase.new(*target_position)
        editor.add_node(reader)

        # Link the reader to the sheet node
        in_socket = reader.contents[0].Socket
        out_socket = sheet.contents[-1].Socket
        editor.add_link(in_socket, out_socket)

        window.activate_action('win.focus-editor')
        # TODO: go to the tab if reusing a sheet

        editor.select_by_click(reader)

        reader.set_data(query, config)

        window.history.grouping = False
