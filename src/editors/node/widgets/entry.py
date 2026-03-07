# entry.py
#
# Copyright 2025 Naufan Rusyda Faikar <hello@naruaika.me>
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

from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Pango
from typing import Any

class NodeEntry(Gtk.Button):

    __gtype_name__ = 'NodeEntry'

    def __init__(self,
                 title:    str,
                 get_data: callable,
                 set_data: callable,
                 ) ->      None:
        """"""
        from ....core.evaluators.arithmetic import Evaluator
        self._evaluator = Evaluator()

        box = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL,
                      spacing     = 6)

        if title:
            label = Gtk.Label(label        = title,
                              xalign       = 0.0,
                              hexpand      = True,
                              ellipsize    = Pango.EllipsizeMode.END,
                              tooltip_text = title)
            box.append(label)

        text = self._transform_text(get_data())

        label = Gtk.Label(label     = text,
                          xalign    = 1.0,
                          ellipsize = Pango.EllipsizeMode.END)
        box.append(label)

        super().__init__(child = box)

        self._title    = title
        self._get_data = get_data
        self._set_data = set_data

        self.connect('clicked', self._on_clicked, label)

    def _transform_text(self,
                        text: str,
                        ) ->  str:
        """"""
        text = str(text)
        self._is_empty = text == ''
        text = text if not self._is_empty else f'[{_('Empty')}]'
        return text

    def _on_clicked(self,
                    button: Gtk.Button,
                    label:  Gtk.Label,
                    ) ->    None:
        """"""
        value = label.get_label() if not self._is_empty else ''
        entry = Gtk.Entry(text             = value,
                          placeholder_text = self._title)

        if isinstance(self._get_data(), (int, float)):
            entry.set_input_purpose(Gtk.InputPurpose.NUMBER)

        entry.add_css_class('node-widget')
        if button.has_css_class('before-socket'):
            entry.add_css_class('before-socket')
        if button.has_css_class('after-socket'):
            entry.add_css_class('after-socket')

        container = button.get_parent()
        container.insert_child_after(entry, button)
        button.unparent()

        args = (container, button, label, entry)

        entry.connect('activate', lambda *_: self._do_apply(args))

        controller = Gtk.EventControllerKey()
        controller.connect('key-pressed', self._on_key_pressed, args)
        entry.add_controller(controller)

        if isinstance(self._get_data(), (int, float)):
            entry.connect('changed', self._on_changed)

        def do_focus() -> bool:
            """"""
            entry.grab_focus()
            return Gdk.EVENT_PROPAGATE

        GLib.timeout_add(50, do_focus)

    def _do_apply(self,
                  args: list[Gtk.Widget],
                  ) ->  None:
        """"""
        container, button, label, entry = args
        text = entry.get_text()

        if isinstance(self._get_data(), (int, float)):
            try:
                text = self._evaluator.evaluate(text)
                if isinstance(self._get_data(), int):
                    text = int(text)
                if isinstance(self._get_data(), float):
                    text = float(text)
            except:
                return

        text = self._transform_text(text)

        label.set_label(text)
        container.insert_child_after(button, entry)
        entry.unparent()

        self._set_data(text)

    def _on_key_pressed(self,
                        event:   Gtk.EventControllerKey,
                        keyval:  int,
                        keycode: int,
                        state:   Gdk.ModifierType,
                        args:    list[Any],
                        ) ->     bool:
        """"""
        if keyval == Gdk.KEY_Escape:
            self._do_apply(args)
            return Gdk.EVENT_STOP
        return Gdk.EVENT_PROPAGATE

    def _on_changed(self,
                    entry: Gtk.Entry,
                    ) ->   None:
        """"""
        text = entry.get_text()
        try:
            text = self._evaluator.evaluate(text)
            if isinstance(self._get_data(), int):
                int(text)
            if isinstance(self._get_data(), float):
                float(text)
        except:
            entry.add_css_class('warning')
        else:
            entry.remove_css_class('warning')

    def get_data(self) -> str:
        """"""
        box = self.get_child()
        label = box.get_last_child()
        return label.get_label()

    def set_data(self,
                 value: str,
                 ) ->   None:
        """"""
        value = self._transform_text(value)

        box = self.get_child()
        label = box.get_last_child()
        label.set_label(value)