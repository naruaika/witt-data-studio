# formula_bar.py
#
# Copyright (c) 2025 Naufan Rusyda Faikar
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
from gi.repository import Gtk
from gi.repository import GtkSource

@Gtk.Template(resource_path = '/com/wittara/studio/sheet/formula_bar.ui')
class SheetFormulaBar(Gtk.Box):
    __gtype_name__ = 'SheetFormulaBar'

    NameBox                = Gtk.Template.Child()
    FormulaBox             = Gtk.Template.Child()
    MultilineFormulaBar    = Gtk.Template.Child()
    MultilineFormulaBox    = Gtk.Template.Child()
    FormulaBarToggleButton = Gtk.Template.Child()
    FormulaBarDataType     = Gtk.Template.Child()

    MARGIN_END = 50

    def __init__(self) -> None:
        """"""
        super().__init__()

        # We override the default behavior of the Gtk.Entry for the name box, so that
        # it willl select all text when the user clicks on it for the first time in a
        # while (when the widget is currently not in focus, to be precise).
        NameBoxText = self.NameBox.get_first_child()
        NameBoxText.set_focus_on_click(False)

        # Add some margin to the formula box to prevent its content from being hidden
        # by the dtype indicator widget.
        FormulaBoxText = self.FormulaBox.get_first_child()
        FormulaBoxText.set_focus_on_click(False)
        FormulaBoxText.set_margin_end(self.MARGIN_END)

        self._setup_name_box()
        self._setup_formula_box()

        self._initialized = False

    def do_map(self) -> None:
        """"""
        if not self._initialized:
            self._setup_actions()
            self._initialized = True
        Gtk.Widget.do_map(self)

    def _setup_name_box(self) -> None:
        """"""
        controller = Gtk.GestureClick()
        controller.connect('pressed', self._on_name_box_pressed)
        self.NameBox.add_controller(controller)

        controller = Gtk.EventControllerFocus()
        controller.connect('leave', self._on_name_box_unfocused)
        self.NameBox.add_controller(controller)

        controller = Gtk.EventControllerKey()
        controller.connect('key-pressed', self._on_name_box_key_pressed)
        self.NameBox.add_controller(controller)

    def _setup_formula_box(self) -> None:
        """"""
        controller = Gtk.GestureClick()
        controller.connect('pressed', self._on_formula_box_pressed)
        self.FormulaBox.add_controller(controller)

        controller = Gtk.EventControllerFocus()
        controller.connect('enter', self._on_formula_box_focused)
        controller.connect('leave', self._on_formula_box_unfocused)
        self.FormulaBox.add_controller(controller)

        controller = Gtk.EventControllerKey()
        controller.connect('key-pressed', self._on_formula_box_key_pressed)
        self.FormulaBox.add_controller(controller)

        controller = Gtk.EventControllerKey()
        controller.connect('key-pressed', self._on_multiline_formula_box_key_pressed)
        self.MultilineFormulaBox.add_controller(controller)

        buffer = self.MultilineFormulaBox.get_buffer()
        buffer.connect('changed', self._on_multiline_formula_box_changed)

        settings = Gtk.Settings.get_default()
        settings.connect('notify::gtk-application-prefer-dark-theme',
                         self._on_prefer_dark_theme_changed)

        self._on_prefer_dark_theme_changed(None, None)

    def _setup_actions(self) -> None:
        """"""
        editor = self.get_editor()

        group = Gio.SimpleActionGroup.new()
        editor.insert_action_group('formula', group)

        controller = Gtk.ShortcutController()
        editor.add_controller(controller)

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
                string_action = f'action(formula.{name})'
                action = Gtk.ShortcutAction.parse_string(string_action)
                shortcut = Gtk.Shortcut.new(trigger, action)
                controller.add_shortcut(shortcut)

        create_action('focus-name-box',     self._focus_name_box_action,
                                            ['<Primary>g'])
        create_action('focus-formula-box',  self._focus_formula_box_action,
                                            ['F2'])
#       create_action('input-formula-box',  self._input_formula_box_action,
#                                           param_type = GLib.VariantType('s'))
        create_action('update-formula-bar', self._update_formula_bar_action,
                                            param_type = GLib.VariantType('as'))

    def _focus_name_box_action(self,
                               action:    Gio.SimpleAction,
                               parameter: GLib.Variant,
                               ) ->       None:
        """"""
        self.NameBox.grab_focus()

    def _focus_formula_box_action(self,
                                  action:    Gio.SimpleAction,
                                  parameter: GLib.Variant) -> None:
        """"""
        editor_in_focus = self.get_focus_child() and \
                          self.FormulaBox.get_focus_child()
        multiline_editor_is_visible = not self.get_focus_child() and \
                                      self.FormulaBarToggleButton.get_active()

        if editor_in_focus or multiline_editor_is_visible:
            self.FormulaBarToggleButton.set_active(True)
            self.MultilineFormulaBox.grab_focus()
            return

        self.FormulaBarToggleButton.set_active(False)
        self.FormulaBox.grab_focus()

#   def _input_formula_box_action(self,
#                                 action:    Gio.SimpleAction,
#                                 parameter: GLib.Variant,
#                                 ) ->       None:
#       """"""
#       input_text = parameter.get_string()
#
#       if self.FormulaBarToggleButton.get_active():
#           self.MultilineFormulaBox.grab_focus()
#           buffer = self.MultilineFormulaBox.get_buffer()
#           GLib.idle_add(buffer.set_text, input_text)
#
#       else:
#           self.FormulaBox.grab_focus()
#           self.FormulaBox.set_text(input_text)
#           self.FormulaBox.select_region(1, 1)

    def _update_formula_bar_action(self,
                                   action:     Gio.SimpleAction,
                                   parameters: list[GLib.Variant],
                                   ) ->        None:
        """"""
        cell_name  = parameters[0]
        cell_data  = parameters[1]
        cell_dtype = parameters[2]

        self.NameBox.set_text(cell_name)
        self.FormulaBox.set_text(cell_data)
        self.FormulaBarDataType.set_text(cell_dtype)

        single_mode_is_enabled = self.FormulaBox.get_visible()
        cell_dtype_isnot_empty = cell_dtype != ''
        is_visible = single_mode_is_enabled and cell_dtype_isnot_empty
        self.FormulaBarDataType.set_visible(is_visible)

        margin_end = self.MARGIN_END if is_visible else 0
        FormulaBoxText = self.FormulaBox.get_first_child()
        FormulaBoxText.set_margin_end(margin_end)

        buffer = self.MultilineFormulaBox.get_buffer()
        GLib.idle_add(buffer.set_text, cell_data)

    @Gtk.Template.Callback()
    def _on_name_box_activated(self,
                               entry: Gtk.Entry,
                               ) ->   None:
        """"""
        from re import fullmatch
        from re import IGNORECASE

        # Normalize the input
        text = entry.get_text()
        text = text.strip()
        text = text.replace(';', ':')
        if text in {'', ':'}:
            text = 'A1'
        if text.startswith(':'):
            text = text[1:]
            text = f'{text}:{text}'
        if text.endswith(':'):
            text = text[:-1]
            text = f'{text}:{text}'

        # Basic check if the input is a valid cell name. Here we accept
        # a wide range of cell name patterns and some non-standard ones
        # that I think will be of use somehow, e.g. A:1 (letter:number)
        # to select the whole sheet. I know that that isn't supposed to
        # be useful, maybe I'm just being lazy after all :)
        cname_pattern = r"[A-Za-z]*\d*|[A-Za-z]*\d*"
        range_pattern = fr"{cname_pattern}(?:[:]{cname_pattern})?"
        if not fullmatch(range_pattern, text, IGNORECASE):
            return

        editor = self.get_editor()
        editor.selection.update_from_name(text)
        editor.grab_focus()

    def _on_name_box_pressed(self,
                             event:   Gtk.GestureClick,
                             n_press: int,
                             x:       float,
                             y:       float,
                             ) ->     None:
        """"""
        # Selects all text when the user clicks on the name box
        # when it's currently not in focus.
        text = self.NameBox.get_text()
        text_length = len(text)
        self.NameBox.select_region(0, text_length)

        NameBoxText = self.NameBox.get_first_child()
        NameBoxText.set_focus_on_click(True)
        NameBoxText.grab_focus()

    def _on_name_box_unfocused(self,
                               event: Gtk.EventControllerFocus,
                               ) ->   None:
        """"""
        NameBoxText = self.NameBox.get_first_child()
        NameBoxText.set_focus_on_click(False)

    def _on_name_box_key_pressed(self,
                                 event:   Gtk.EventControllerKey,
                                 keyval:  int,
                                 keycode: int,
                                 state:   Gdk.ModifierType,
                                 ) ->     bool:
        """"""
        # Pressing tab key will reset the name box instead of activating
        # the name box to prevent undesired behaviors. I have seen other
        # applications don't do this, but I prefer this for consistency.
        if keyval == Gdk.KEY_Tab:
            editor = self.get_editor()
            editor.update_formula_bar()
            return False

        if keyval in {Gdk.KEY_Up, Gdk.KEY_Down}:
            return True # keep the focus on the name box

        return False

    @Gtk.Template.Callback()
    def _on_formula_box_changed(self,
                                entry: Gtk.Entry,
                                ) ->   None:
        """"""
        pass

    @Gtk.Template.Callback()
    def _on_formula_box_deleted(self,
                                entry:     Gtk.Entry,
                                start_pos: int,
                                end_pos:   int,
                                ) ->       None:
        """"""
        pass

    @Gtk.Template.Callback()
    def _on_formula_box_activated(self,
                                  entry: Gtk.Entry,
                                  ) ->   None:
        """"""
        text = entry.get_text()

        # TODO

    def _on_formula_box_pressed(self,
                                event:   Gtk.GestureClick,
                                n_press: int,
                                x:       float,
                                y:       float,
                                ) ->     None:
        """"""
        # Selects all text when the user clicks on the formula box
        # when it's currently not in focus.
        text = self.FormulaBox.get_text()
        self.FormulaBox.select_region(0, len(text))

        FormulaBoxText = self.FormulaBox.get_first_child()
        FormulaBoxText.set_focus_on_click(True)
        FormulaBoxText.grab_focus()

    def _on_formula_box_focused(self,
                                event: Gtk.EventControllerFocus,
                                ) ->   None:
        """"""
        pass

    def _on_formula_box_unfocused(self,
                                  event: Gtk.EventControllerFocus,
                                  ) ->   None:
        """"""
        FormulaBoxText = self.FormulaBox.get_first_child()
        FormulaBoxText.set_focus_on_click(False)

    def _on_formula_box_key_pressed(self,
                                    event:   Gtk.EventControllerKey,
                                    keyval:  int,
                                    keycode: int,
                                    state:   Gdk.ModifierType,
                                    ) ->     bool:
        """"""
        if keyval in {Gdk.KEY_Up, Gdk.KEY_Down}:
            return True # keep the focus on the formula box
        return False

    def _on_multiline_formula_box_changed(self,
                                          buffer: GtkSource.Buffer,
                                          ) ->    None:
        """"""
        pass

    def _on_multiline_formula_box_key_pressed(self,
                                              event:   Gtk.EventControllerKey,
                                              keyval:  int,
                                              keycode: int,
                                              state:   Gdk.ModifierType,
                                              ) ->     bool:
        """"""
        # Only pressing Control+Return keys that'll trigger the execution.
        if keyval == Gdk.KEY_Return:
            if state != Gdk.ModifierType.CONTROL_MASK:
                return False

            buffer = self.MultilineFormulaBox.get_buffer()
            start_iter = buffer.get_start_iter()
            end_iter = buffer.get_end_iter()
            text = buffer.get_text(start_iter, end_iter, True)

            # TODO

            return True

        return False

    def _on_prefer_dark_theme_changed(self,
                                      settings:     Gtk.Settings,
                                      gparamstring: str,
                                      ) ->          None:
        """"""
        scheme_manager = GtkSource.StyleSchemeManager.get_default()
        prefers_dark = Adw.StyleManager().get_dark()
        color_scheme = 'Adwaita-dark' if prefers_dark else 'Adwaita'
        style_scheme = scheme_manager.get_scheme(color_scheme)

        buffer = self.MultilineFormulaBox.get_buffer()
        buffer.set_style_scheme(style_scheme)

    @Gtk.Template.Callback()
    def _on_toggle_formula_bar_toggled(self,
                                       button: Gtk.ToggleButton,
                                       ) ->           None:
        """"""
        # Multi-line mode is active
        if multiline_mode := button.get_active():
            text = self.FormulaBox.get_text()
            buffer = self.MultilineFormulaBox.get_buffer()
            GLib.idle_add(buffer.set_text, text)
            self.MultilineFormulaBox.grab_focus()

        # Single-line mode is active
        else:
            buffer = self.MultilineFormulaBox.get_buffer()
            start_iter = buffer.get_start_iter()
            end_iter = buffer.get_end_iter()
            text = buffer.get_text(start_iter, end_iter, True)
            self.FormulaBox.set_text(text)
            self.FormulaBox.grab_focus()

        self.FormulaBox.set_visible(not multiline_mode)
        self.MultilineFormulaBar.set_visible(multiline_mode)

        single_mode_is_enabled = self.FormulaBox.get_visible()
        cell_dtype_isnot_empty = self.FormulaBarDataType.get_text() != ''
        is_visible = single_mode_is_enabled and cell_dtype_isnot_empty
        self.FormulaBarDataType.set_visible(is_visible)

        margin_end = self.MARGIN_END if is_visible else 0
        FormulaBoxText = self.FormulaBox.get_first_child()
        FormulaBoxText.set_margin_end(margin_end)

    def get_editor(self) -> 'SheetEditor':
        """"""
        box = self.get_parent()
        editor = box.get_parent()
        return editor

from .editor import SheetEditor
