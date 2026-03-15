# entry.py
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
        value = entry.get_text()

        if isinstance(self._get_data(), (int, float)):
            try:
                value = self._evaluator.evaluate(value)
                if isinstance(self._get_data(), int):
                    value = int(value)
                if isinstance(self._get_data(), float):
                    value = float(value)
            except:
                return

        text = self._transform_text(value)

        label.set_label(text)
        container.insert_child_after(button, entry)
        entry.unparent()

        self._set_data(value)

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
        text = self._transform_text(value)

        box = self.get_child()
        label = box.get_last_child()
        label.set_label(text)