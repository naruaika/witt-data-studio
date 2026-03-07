# time_picker.py
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
import datetime

from ....ui.time_picker import TimePicker

class NodeTimePicker(Gtk.Button):

    __gtype_name__ = 'NodeTimePicker'

    def __init__(self,
                 get_data: callable,
                 set_data: callable,
                 ) ->      None:
        """"""
        box = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL,
                      spacing     = 6)

        label = Gtk.Label(label     = self._transform_text(get_data()),
                          xalign    = 1.0,
                          ellipsize = Pango.EllipsizeMode.END)
        box.append(label)

        super().__init__(child = box)

        self._get_data = get_data
        self._set_data = set_data

        entry = Gtk.Entry()
        entry.add_css_class('node-widget')

        if self.has_css_class('before-socket'):
            entry.add_css_class('before-socket')
        if self.has_css_class('after-socket'):
            entry.add_css_class('after-socket')

        picker = TimePicker(halign = Gtk.Align.CENTER,
                            valign = Gtk.Align.CENTER)
        popover = Gtk.Popover(child = picker)

        picker.set_hour(get_data().hour)
        picker.set_minute(get_data().minute)
        picker.set_second(get_data().second)

        picker.connect('time-updated', self._on_picker_updated, entry)

        entry.connect('changed', self._on_entry_changed, picker)

        entry.set_icon_from_icon_name(icon_pos  = Gtk.EntryIconPosition.SECONDARY,
                                      icon_name = 'vcal-symbolic')
        entry.connect('icon-press', self._on_icon_pressed, picker, popover)

        popover.set_parent(entry)

        self.connect('clicked', self._on_clicked, entry, label, picker)

        # def on_icon_pressed(entry:    Gtk.Entry,
        #                     icon_pos: Gtk.EntryIconPosition,
        #                     ) ->      None:
        #     """"""
        #     if icon_pos == Gtk.EntryIconPosition.SECONDARY:
        #         picker.set_mode(picker.MODE_HOUR)
        #         rect = entry.get_icon_area(icon_pos)
        #         popover.set_pointing_to(rect)
        #         popover.popup()

        # entry.set_icon_from_icon_name(icon_pos  = Gtk.EntryIconPosition.SECONDARY,
        #                               icon_name = 'clock-alt-symbolic')
        # entry.connect('icon-press', on_icon_pressed)

    def _transform_text(self,
                        text: str,
                        ) ->  str:
        """"""
        text = str(text)
        self._is_empty = text == ''
        text = text if not self._is_empty else f'[{_('Empty')}]'
        return text

    def _on_picker_updated(self,
                           picker: TimePicker,
                           entry:  Gtk.Entry,
                           ) ->    None:
        """"""
        value: datetime.time = self._get_data()
        value = value.replace(picker.get_hour(),
                              picker.get_minute(),
                              picker.get_second())
        value = value.strftime('%H:%M:%S')

        if entry.get_text() != value:
            entry.remove_css_class('warning')
            entry.set_text(value)

    def _on_entry_changed(self,
                          entry:  Gtk.Entry,
                          picker: TimePicker,
                          ) ->    None:
        """"""
        text = entry.get_text()
        self._do_apply(text, entry, picker, submit = False)

    def _on_icon_pressed(self,
                         entry:    Gtk.Entry,
                         icon_pos: Gtk.EntryIconPosition,
                         picker:   TimePicker,
                         popover:  Gtk.Popover,
                         ) ->      None:
        """"""
        if icon_pos == Gtk.EntryIconPosition.SECONDARY:
            picker.set_mode(picker.MODE_HOUR)
            rect = entry.get_icon_area(icon_pos)
            popover.set_pointing_to(rect)
            popover.popup()

    def _on_clicked(self,
                    button: Gtk.Button,
                    entry:  Gtk.Entry,
                    label:  Gtk.Label,
                    picker: TimePicker,
                    ) ->    None:
        """"""
        text = self._transform_text(label.get_label())
        entry.set_text(text)

        container = button.get_parent()
        container.insert_child_after(entry, button)
        button.unparent()

        args = (container, button, label, picker, entry)

        entry.connect('activate', lambda *_: self._do_update(args))

        controller = Gtk.EventControllerKey()
        controller.connect('key-pressed', self._on_key_pressed, args)
        entry.add_controller(controller)

        def do_focus() -> bool:
            """"""
            entry.grab_focus()
            return Gdk.EVENT_PROPAGATE

        GLib.timeout_add(50, do_focus)

    def _do_apply(self,
                  value:  str,
                  entry:  Gtk.Entry,
                  picker: TimePicker,
                  submit: bool,
                  ) ->    None:
        """"""
        try:
            value = datetime.date.fromisoformat(value)
        except:
            entry.add_css_class('warning')
        else:
            entry.remove_css_class('warning')
            picker.set_hour(value.hour)
            picker.set_minute(value.minute)
            picker.set_second(value.second)

            if submit:
                self._set_data(value)

    def _do_update(self,
                   args: list[Any],
                   ) ->  None:
        """"""
        container, button, label, picker, entry = args

        text = entry.get_text()
        text = self._transform_text(text)

        label.set_label(text)
        container.insert_child_after(button, entry)
        entry.unparent()

        self._do_apply(text, entry, picker, sumbit = True)

    def _on_key_pressed(self,
                        event:   Gtk.EventControllerKey,
                        keyval:  int,
                        keycode: int,
                        state:   Gdk.ModifierType,
                        args:    list[Any],
                        ) ->     bool:
        """"""
        if keyval == Gdk.KEY_Escape:
            self._do_update(args)
            return Gdk.EVENT_STOP
        return Gdk.EVENT_PROPAGATE

    def set_data(self,
                 value: str,
                 ) ->   None:
        """"""
        box = self.get_child()
        label = box.get_last_child()
        label.set_label(str(value))