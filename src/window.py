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

from .core.action import Action
from .core.history import History

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
    StatusBar   = Gtk.Template.Child()

    def __init__(self, **kwargs) -> None:
        """"""
        nodes  = kwargs.get('nodes',  [])
        links  = kwargs.get('links',  [])
        viewer = kwargs.get('viewer', None)

        if 'nodes' in kwargs:
            del kwargs['nodes']
        if 'links' in kwargs:
            del kwargs['links']
        if 'viewer' in kwargs:
            del kwargs['viewer']

        super().__init__(**kwargs)

        self.file_path:    str  = None
        self.file_saved:   bool = True
        self.command_list: list = []

        self.history = History()

        self._setup_uinterfaces()
        self._setup_controllers()

        self._setup_actions()
        self._setup_commands()

        self._setup_node_editor(nodes, links, viewer)

    def do_close_request(self) -> bool:
        """"""
        if self.file_saved:
            return Gdk.EVENT_PROPAGATE

        dialog = Adw.AlertDialog()

        dialog.set_heading(_('Close Window?'))
        dialog.set_body(_('Any unsaved work will be lost permanently. '
                          'This action cannot be undone.'))

        dialog.add_response('cancel', _('Ca_ncel'))
        dialog.add_response('close', _('_Close'))

        dialog.set_response_appearance('close', Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response('close')
        dialog.set_close_response('cancel')

        def on_dismissed(dialog: Adw.AlertDialog,
                         result: Gio.Task,
                         ) ->    None:
            """"""
            if result.had_error():
                return
            if dialog.choose_finish(result) != 'close':
                return
            self.file_saved = True #
            self.close()

        dialog.choose(self, None, on_dismissed)

        return Gdk.EVENT_STOP

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
        create_action('focus-editor',       self._on_focus_editor_action)

        create_action('undo',               lambda *_: self.undo(),
                                            ['<Primary>z'])
        create_action('redo',               lambda *_: self.redo(),
                                            ['<Shift><Primary>z'])

        create_action('save',               self._on_save,
                                            ['<Primary>s'])
        create_action('save-as',            self._on_save_as,
                                            ['<Shift><Primary>s'])

        # Just want to make it explicit that I'm using this
        # action to trick the application' action lookup so
        # that the target menu items become insensitive >_<
        disabled = Gio.SimpleAction.new('toolbar.disabled')
        disabled.set_enabled(False)
        self.add_action(disabled)

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

        create_command('app.new-window',    _('New Window'),
                                            shortcuts = ['<Shift><Primary>N'])

        create_command('win.close-editor',  _('Close Editor'),
                                            shortcuts = ['<Primary>w'])
        create_command('win.close-window',  _('Close Window'),
                                            shortcuts = ['<Alt>F4'])
        create_command('win.focus-editor',  _('Focus Editor'),
                                            shortcuts = ['Escape'])

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
        if self.CommandPalette.get_visible():
            self.CommandPalette.popdown()

        if editor := self.get_selected_editor():
            editor.refresh_ui()
            editor.grab_focus()

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

        key_event_controller = Gtk.EventControllerKey()
        key_event_controller.connect('key-pressed', self._on_key_pressed)
        self.add_controller(key_event_controller)

        self.TabView.connect('notify::selected-page', self._on_page_changed)
        self.TabView.connect('close-page', self._on_page_closed)

    def _setup_node_editor(self,
                           nodes:  list[NodeFrame] = [],
                           links:  list[NodeLink]  = [],
                           viewer: NodeFrame       = None,
                           ) ->    None:
        """"""
        self.node_editor = None
        self.node_editor = NodeEditor(nodes, links)
        self.add_new_editor(self.node_editor, pinned = True)

        if not viewer:
            from .node.repository import NodeViewer
            for node in nodes:
                if isinstance(node.parent, NodeViewer):
                    viewer = node
                    break

        def do_view(viewer: NodeFrame) -> None:
            """"""
            self.history.freezing = True
            self.node_editor.select_viewer(viewer)
            self.history.freezing = False

        GLib.idle_add(do_view, viewer)

    def _on_resized(self,
                    widget:     Gtk.Widget,
                    param_spec: GObject.ParamSpec,
                    ) ->        None:
        """"""
        editors = self.get_all_editors()
        for editor in editors:
            editor.queue_resize()

    def _on_key_pressed(self,
                        event:   Gtk.EventControllerKey,
                        keyval:  int,
                        keycode: int,
                        state:   Gdk.ModifierType,
                        ) ->     bool:
        """"""
        if keyval == Gdk.KEY_Escape:
            self.activate_action('win.focus-editor')
            return True

        return False

    def _on_page_changed(self,
                         widget:     Gtk.Widget,
                         param_spec: GObject.ParamSpec,
                         ) ->        None:
        """"""
        self.Toolbar.populate()
        self.StatusBar.populate()

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

    def do(self,
           action:   Action,
           undoable: bool = True,
           add_only: bool = False,
           ) ->      bool:
        """"""
        editor = self.get_selected_editor()
        action.coown = editor

        success = self.history.do(action,
                                  undoable,
                                  add_only)

        self._post_do()

        if add_only:
            return True

        if not success:
            return False

        if editor := self.get_selected_editor():
            editor.refresh_ui()
            editor.grab_focus()

        return True

    def undo(self) -> bool:
        """"""
        # Prevent from colliding with the undo action of editable widgets
        focused_widget = self.get_focus()
        if isinstance(focused_widget, (Gtk.Text, Gtk.TextView)):
            focused_widget.activate_action('text.undo', None)
            return True

        (success, actions) = self.history.undo()

        if actions:
            first_action = actions[0]
            owner = first_action.owner
            coown = first_action.coown
            self.go_to_editor([owner, coown])

        if editor := self.get_selected_editor():
            editor.refresh_ui()
            editor.grab_focus()

        self._post_undo()

        return success

    def redo(self) -> bool:
        """"""
        # Prevent from colliding with the undo action of editable widgets
        focused_widget = self.get_focus()
        if isinstance(focused_widget, (Gtk.Text, Gtk.TextView)):
            focused_widget.activate_action('text.redo', None)
            return True

        (success, actions) = self.history.redo()

        if actions:
            first_action = actions[0]
            owner = first_action.owner
            coown = first_action.coown
            self.go_to_editor([owner, coown])

        if editor := self.get_selected_editor():
            editor.refresh_ui()
            editor.grab_focus()

        self._post_do()

        return success

    def _post_do(self) -> None:
        """"""
        if not self.history.undo_stack:
            return

        from .node.action import ActionSelectByClick
        from .node.action import ActionSelectByRubberband
        classes = (ActionSelectByClick, ActionSelectByRubberband)
        last_action = self.history.undo_stack[-1]
        is_selection = isinstance(last_action, classes)
        if not (is_selection and not last_action.group):
            self.StatusBar.set_file_saved(False)
            self.file_saved = False

    def _post_undo(self) -> None:
        """"""
        if not self.history.redo_stack:
            return

        from .node.action import ActionSelectByClick
        from .node.action import ActionSelectByRubberband
        classes = (ActionSelectByClick, ActionSelectByRubberband)
        last_action = self.history.redo_stack[-1]
        is_selection = isinstance(last_action, classes)
        if not (is_selection and not last_action.group):
            self.StatusBar.set_file_saved(False)
            self.file_saved = False

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

    def go_to_editor(self,
                     editor: Editor,
                     ) ->    None:
        """"""
        from .core.utils import isiterable
        if not isiterable(editor):
            editor = [editor]

        # This is an edge case that only occurs
        # when loading a workbook file, TODO?
        if None in editor:
            editor.remove(None)
            editor.append(self.node_editor)

        if self.get_selected_editor() in editor:
            return

        for page in self.TabView.get_pages():
            if page.get_child() in editor:
                self.TabView.set_selected_page(page)
                break

        self.present()
