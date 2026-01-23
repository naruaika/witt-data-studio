# window.py
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
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gtk
from typing import TypeAlias

from .node.editor import NodeEditor
from .sheet.editor import SheetEditor
from .chart.editor import ChartEditor

from .node.frame import NodeFrame
from .node.link import NodeLink

Editor: TypeAlias = NodeEditor  | \
                    ChartEditor | \
                    SheetEditor

@Gtk.Template(resource_path = '/com/macipra/witt/window.ui')
class Window(Adw.ApplicationWindow):

    __gtype_name__ = 'Window'

    TitleBar    = Gtk.Template.Child()
    TabBar      = Gtk.Template.Child()
    TabView     = Gtk.Template.Child()
    TabButton   = Gtk.Template.Child()
    TabOverview = Gtk.Template.Child()
    Toolbar     = Gtk.Template.Child()
    Container   = Gtk.Template.Child()

    def __init__(self, **kwargs) -> None:
        """"""
        nodes = kwargs.get('nodes', [])
        links = kwargs.get('links', [])

        if 'nodes' in kwargs:
            del kwargs['nodes']
        if 'links' in kwargs:
            del kwargs['links']

        super().__init__(**kwargs)

        self.file_path:    str  = None
        self.command_list: list = []

        self._setup_uinterfaces()
        self._setup_controllers()

        self._setup_actions()
        self._setup_commands()

        self._setup_node_editor(nodes, links)

    def _setup_uinterfaces(self) -> None:
        """"""
        button = self.TabButton.get_first_child()
        button.add_css_class('flat')

        from .command_palette import CommandPalette
        self.CommandPalette = CommandPalette()
        self.Container.add_overlay(self.CommandPalette)

    def _setup_actions(self) -> None:
        """"""
        group = Gio.SimpleActionGroup.new()
        self.insert_action_group('win', group)

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
                action = Gtk.ShortcutAction.parse_string(f'action(win.{name})')
                shortcut = Gtk.Shortcut.new(trigger, action)
                self.add_shortcut(shortcut)

                application = self.get_application()
                application.set_accels_for_action(f'win.{name}', shortcuts)

        create_action('command-palette',    self._on_command_palette_action,
                                            ['F1'])
        create_action('toolbar',            self._on_toolbar_action,
                                            param_type = GLib.VariantType('s'))

        create_action('close-editor',       self._on_close_editor_action,
                                            ['<Primary>w'])
        create_action('close-window',       self._on_close_window_action,
                                            ['<Alt>F4'])
        create_action('focus-editor',       self._on_focus_editor_action,
                                            ['Escape'])

        create_action('undo',               self._on_undo,
                                            ['<Primary>z'])
        create_action('redo',               self._on_redo,
                                            ['<Shift><Primary>z'])

        create_action('save',               self._on_save,
                                            ['<Primary>s'])
        create_action('save-as',            self._on_save_as,
                                            ['<Shift><Primary>s'])

    def _setup_commands(self) -> None:
        """"""
        def create_command(action_name: str,
                           title:       str,
                           action_args: GLib.Variant = None,
                           shortcuts:   list[str]    = [],
                           ) ->         None:
            """"""
            self.command_list.append({
                'action-name': action_name,
                'action-args': action_args,
                'title':       title,
                'shortcuts':   shortcuts,
            })

        create_command('app.about',         _('About Application'),
                                            shortcuts = ['F12'])
        create_command('app.exit',          _('Exit Application'),
                                            shortcuts = ['<Primary>q'])

        create_command('win.close-editor',  _('Close Editor'),
                                            shortcuts = ['<Primary>w'])
        create_command('win.close-window',  _('Close Window'),
                                            shortcuts = ['<Alt>F4'])
        create_command('win.focus-editor',  _('Focus Editor'),
                                            shortcuts = ['Escape'])

        # TODO: add context for undo and redo command

        create_command('win.undo',          _('Undo'),
                                            shortcuts = ['<Primary>z'])
        create_command('win.redo',          _('Redo'),
                                            shortcuts = ['<Shift><Primary>z'])

        create_command('win.save',          _('Save'),
                                            shortcuts = ['<Primary>s'])
        create_command('win.save-as',       _('Save As...'),
                                            shortcuts = ['<Shift><Primary>s'])
    def _on_command_palette_action(self,
                                   action:    Gio.SimpleAction,
                                   parameter: GLib.Variant,
                                   ) ->       None:
        """"""
        command_list = []

        for command in self.command_list:
            command_list.append(command)

        if editor := self.get_selected_editor():
            if hasattr(editor, 'get_command_list'):
                for command in editor.get_command_list():
                    command_list.append(command)

        if not command_list:
            return

        command_list.sort(key = lambda cmd: cmd['title'])

        self.CommandPalette.popup(command_list)

    def _on_toolbar_action(self,
                           action:    Gio.SimpleAction,
                           parameter: GLib.Variant,
                           ) ->       None:
        """"""
        editor = self.get_selected_editor()

        action_name = parameter.get_string()
        action_name = f'{editor.ACTION_PREFIX}.{action_name}'

        editor.activate_action(action_name)
        editor.refresh_ui()
        editor.grab_focus()

    def _on_close_editor_action(self,
                                action:    Gio.SimpleAction,
                                parameter: GLib.Variant,
                                ) ->       None:
        """"""
        if tab_page := self.TabView.get_selected_page():
            self.TabView.close_page(tab_page)

    def _on_close_window_action(self,
                                action:    Gio.SimpleAction,
                                parameter: GLib.Variant,
                                ) ->       None:
        """"""
        self.close()

    def _on_focus_editor_action(self,
                                action:    Gio.SimpleAction,
                                parameter: GLib.Variant,
                                ) ->       None:
        """"""
        if editor := self.get_selected_editor():
            editor.refresh_ui()
            editor.grab_focus()

        if self.CommandPalette.get_visible():
            self.CommandPalette.popdown()

    def _on_undo(self,
                 action:    Gio.SimpleAction,
                 parameter: GLib.Variant,
                 ) ->       None:
        """"""
        editor = self.get_selected_editor()
        editor.undo()

    def _on_redo(self,
                 action:    Gio.SimpleAction,
                 parameter: GLib.Variant,
                 ) ->       None:
        """"""
        editor = self.get_selected_editor()
        editor.redo()

    def _on_save(self,
                 action:    Gio.SimpleAction,
                 parameter: GLib.Variant,
                 ) ->       None:
        """"""
        application = self.get_application()
        application.save(self)

    def _on_save_as(self,
                    action:    Gio.SimpleAction,
                    parameter: GLib.Variant,
                    ) ->       None:
        """"""
        application = self.get_application()
        application.save_as(self)

    def _setup_controllers(self) -> None:
        """"""
        self.connect('notify::default-height', self._on_resized)
        self.connect('notify::default-width', self._on_resized)
        self.connect('notify::fullscrened', self._on_resized)
        self.connect('notify::maximized', self._on_resized)

        self.TabView.connect('notify::selected-page', self._on_page_changed)
        self.TabView.connect('close-page', self._on_page_closed)

    def _setup_node_editor(self,
                           nodes: list['NodeFrame'] = [],
                           links: list['NodeLink']  = [],
                           ) ->   None:
        """"""
        self.node_editor = NodeEditor(nodes, links)
        self.add_new_editor(self.node_editor, pinned = True)

    def _on_resized(self,
                    widget:     Gtk.Widget,
                    param_spec: GObject.ParamSpec,
                    ) ->        None:
        """"""
        editors = self.get_all_editors()
        for editor in editors:
            editor.queue_resize()

    def _on_page_changed(self,
                         widget:     Gtk.Widget,
                         param_spec: GObject.ParamSpec,
                         ) ->        None:
        """"""
        self.Toolbar.populate()

        # TODO: update undo/redo menu item

        editor = self.get_selected_editor()
        editor.grab_focus()

        if self.CommandPalette.get_visible():
            self.CommandPalette.popdown()

    def _on_page_closed(self,
                        tab_view: Adw.TabView,
                        tab_page: Adw.TabPage,
                        ) ->      bool:
        """"""
        self.node_editor.do_close_page(tab_page)
        return Gdk.EVENT_PROPAGATE

    @Gtk.Template.Callback()
    def _on_tab_button_clicked(self,
                               button: Gtk.Button,
                               ) ->    None:
        """"""
        self.TabOverview.set_open(True)

    def add_new_editor(self,
                       editor: Editor,
                       pinned: bool = False,
                       ) ->    Adw.TabPage:
        """"""
        if pinned:
            page = self.TabView.append_pinned(editor)
        else:
            page = self.TabView.append(editor)

        indicator_icon = Gio.ThemedIcon.new(editor.ICON_NAME)
        page.set_indicator_icon(indicator_icon)

        page.bind_property('title', editor, 'title', GObject.BindingFlags.BIDIRECTIONAL)
        page.set_title(editor.title)

        self.TabView.set_selected_page(page)

        editor.setup()
        editor.grab_focus()

        return page

    def get_all_editors(self) -> list[Editor]:
        """"""
        return [page.get_child() for page in self.TabView.get_pages()]

    def get_selected_editor(self) -> Editor:
        """"""
        if page := self.TabView.get_selected_page():
            return page.get_child()
        return None
