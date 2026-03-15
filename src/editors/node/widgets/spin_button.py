# spin_button.py
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

class NodeSpinButton(Gtk.Button):

    __gtype_name__ = 'NodeSpinButton'

    def __init__(self,
                 title:    str,
                 get_data: callable,
                 set_data: callable,
                 lower:    float = None,
                 upper:    float = None,
                 digits:   int   = 3,
                 ) ->      None:
        """"""
        box = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL,
                      spacing     = 6)

        label = Gtk.Label(label        = title,
                          xalign       = 0.0,
                          hexpand      = True,
                          ellipsize    = Pango.EllipsizeMode.END,
                          tooltip_text = title)
        box.append(label)

        label = Gtk.Label(label     = get_data(),
                          xalign    = 1.0,
                          ellipsize = Pango.EllipsizeMode.END)
        box.append(label)

        super().__init__(child = box)

        self._get_data = get_data
        self._set_data = set_data
        self._lower    = lower
        self._upper    = upper
        self._digits   = digits

        args = (label, lower, upper)
        self.connect('clicked', self._on_clicked, *args)

    def _on_clicked(self,
                    button: Gtk.Button,
                    label:  Gtk.Label,
                    lower:  float,
                    upper:  float,
                    ) ->    None:
        """"""
        value = label.get_label()
        value = int(value) if self._digits == 0 else float(value)
        lower = -GLib.MAXDOUBLE if lower is None else lower
        upper = +GLib.MAXDOUBLE if upper is None else upper

        adjustment = Gtk.Adjustment(value          = value,
                                    lower          = lower,
                                    upper          = upper,
                                    step_increment = 1,
                                    page_increment = 10,
                                    page_size      = 10)
        spin = Gtk.SpinButton(numeric    = True,
                              adjustment = adjustment,
                              hexpand    = True,
                              digits     = self._digits)

        spin.add_css_class('node-widget')
        if button.has_css_class('before-socket'):
            spin.add_css_class('before-socket')
        if button.has_css_class('after-socket'):
            spin.add_css_class('after-socket')

        container = button.get_parent()
        container.insert_child_after(spin, button)
        button.unparent()

        args = (container, button, label, spin)
        text = spin.get_first_child()

        text.connect('activate', lambda *_: self._do_apply(args))

        controller = Gtk.EventControllerKey()
        controller.connect('key-pressed', self._on_key_pressed, args)
        text.add_controller(controller)

        def do_focus() -> bool:
            """"""
            spin.grab_focus()
            return Gdk.EVENT_PROPAGATE

        GLib.timeout_add(50, do_focus)

    def _do_apply(self,
                  args: list[Gtk.Widget],
                  ) ->  None:
        """"""
        container, button, label, spin = args

        value = spin.get_value()
        value = int(value) if self._digits == 0 else float(value)

        label.set_label(str(value))
        container.insert_child_after(button, spin)
        spin.unparent()

        self._set_data(value)

    def _on_key_pressed(self,
                        event:   Gtk.EventControllerKey,
                        keyval:  int,
                        keycode: int,
                        state:   Gdk.ModifierType,
                        args:    list[Gtk.Widget],
                        ) ->     bool:
        """"""
        if keyval == Gdk.KEY_Escape:
            self._do_apply(args)
            return Gdk.EVENT_STOP
        return Gdk.EVENT_PROPAGATE

    def set_data(self,
                 value: float,
                 ) ->   None:
        """"""
        box = self.get_child()
        label = box.get_last_child()
        label.set_label(str(value))