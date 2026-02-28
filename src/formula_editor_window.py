# formula_editor_window.py
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
from gi.repository import Gtk
from gi.repository import GtkSource

@Gtk.Template(resource_path = '/com/wittara/studio/formula_editor_window.ui')
class FormulaEditorWindow(Adw.Window):

    __gtype_name__ = 'FormulaEditorWindow'

    WindowTitle = Gtk.Template.Child()
    SourceView  = Gtk.Template.Child()
    ApplyButton = Gtk.Template.Child()

    def __init__(self,
                 subtitle:      str,
                 callback:      callable,
                 transient_for: Gtk.Window,
                 application:   Gtk.Application,
                 formula:       str = None,
                 ) ->           None:
        """"""
        super().__init__(transient_for = transient_for,
                         application   = application)

        self.callback = callback

        if subtitle:
            self.WindowTitle.set_subtitle(subtitle)

        self._setup_source_view()
        self._setup_controllers()

        self.SourceBuffer.set_text(formula or 'value')

    def _setup_source_view(self) -> None:
        """"""
        language_manager = GtkSource.LanguageManager.get_default()
        language = language_manager.get_language('python')

        self.SourceBuffer = GtkSource.Buffer(language         = language,
                                             highlight_syntax = True)
        self.SourceView.set_buffer(self.SourceBuffer)

        settings = Gtk.Settings.get_default()
        settings.connect('notify::gtk-application-prefer-dark-theme',
                         self._on_prefer_dark_theme_changed)

        self._on_prefer_dark_theme_changed(None, None)

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

        if keyval == Gdk.KEY_F5:
            self._apply()
            return Gdk.EVENT_STOP

        return Gdk.EVENT_PROPAGATE

    @Gtk.Template.Callback()
    def _on_apply_button_clicked(self,
                                 button: Gtk.Button,
                                 ) ->    None:
        """"""
        self._apply()

    def _apply(self) -> None:
        """"""
        start_iter = self.SourceBuffer.get_start_iter()
        end_iter = self.SourceBuffer.get_end_iter()

        formula = self.SourceBuffer.get_text(start_iter, end_iter, True)
        formula = formula.strip()

        self.close()

        self.callback(formula)