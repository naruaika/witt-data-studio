# command_palette.py
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
from gi.repository import GLib
from gi.repository import Gio
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Pango

class CommandListItem(GObject.Object):

    __gtype_name__ = 'CommandListItem'

    action_name    = GObject.Property(type = str, default = '')
    title          = GObject.Property(type = str, default = 'Command')
    label          = GObject.Property(type = str, default = 'Command')

    is_separator   = GObject.Property(type = bool, default = False)
    is_recent_item = GObject.Property(type = bool, default = False)

    shortcuts: list[str] = []

    def __init__(self,
                 action_name:     str          = '',
                 action_args:     GLib.Variant = None,
                 title:           str          = '',
                 shortcuts:       list[str]    = [],
                 is_separator:    bool         = False,
                 is_recent_item:  bool         = False,
                 ) ->             None:
        """"""
        super().__init__()

        self.action_name    = action_name
        self.action_args    = action_args
        self.title          = title
        self.label          = title
        self.shortcuts      = shortcuts or []
        self.is_separator   = is_separator
        self.is_recent_item = is_recent_item


@Gtk.Template(resource_path = '/com/wittara/studio/command_palette.ui')
class CommandPalette(Adw.Bin):

    __gtype_name__ = 'CommandPalette'

    Entry          = Gtk.Template.Child()
    ScrolledWindow = Gtk.Template.Child()
    ListView       = Gtk.Template.Child()
    Selection      = Gtk.Template.Child()
    ListStore      = Gtk.Template.Child()

    MAX_RECENT_COMMANDS = 10

    def __init__(self) -> None:
        """"""
        super().__init__()

        key_event_controller = Gtk.EventControllerKey()
        key_event_controller.connect('key-pressed', self._on_key_pressed)
        self.add_controller(key_event_controller)

        factory = Gtk.SignalListItemFactory()
        factory.connect('setup', self._setup_factory)
        factory.connect('bind', self._bind_factory)
        factory.connect('unbind', self._unbind_factory)
        self.ListView.set_factory(factory)

        self.command_titles = []

        self.is_updating_ui = False

    def popup(self,
              command_list: list[dict],
              ) ->          None:
        """"""
        if self.get_visible():
            self.Entry.grab_focus()
            return

        self.command_titles = []
        self.ListStore.remove_all()

        for command in command_list:
            if command['title'] == '$placeholder':
                continue
            list_item = CommandListItem(command['action-name'],
                                        command['action-args'],
                                        command['title'],
                                        command['shortcuts'])
            self.command_titles.append(list_item.title)
            self.ListStore.append(list_item)

        self.Entry.set_text('')
        self.Entry.grab_focus()

        self.set_visible(True)

        self._refresh_ui()

        # To prevent the command palette from being closed
        # immediately especially after opening from a menu
        def stop_updating_ui() -> None:
            self.is_updating_ui = False
        self.is_updating_ui = True
        GLib.timeout_add(200, stop_updating_ui)

    def popdown(self) -> None:
        """"""
        self.set_visible(False)

        window = self.get_root()
        window.activate_action('win.focus-editor')

    def _setup_factory(self,
                       list_item_factory: Gtk.SignalListItemFactory,
                       list_item:         Gtk.ListItem,
                       ) ->               None:
        """"""
        list_item.set_focusable(False)

        box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        list_item.set_child(box)

        content = Gtk.CenterBox(orientation = Gtk.Orientation.HORIZONTAL)
        box.append(content)

        label = Gtk.Label(halign     = Gtk.Align.START,
                          ellipsize  = Pango.EllipsizeMode.END,
                          use_markup = True)
        content.set_start_widget(label)

        shortcut = Gtk.Label(halign = Gtk.Align.END)
        shortcut.add_css_class('dimmed')
        content.set_end_widget(shortcut)

        separator = Gtk.Separator(orientation = Gtk.Orientation.HORIZONTAL,
                                  visible     = False)
        box.append(separator)

        list_item.content = content
        list_item.label = label
        list_item.shortcut = shortcut
        list_item.separator = separator
        list_item.highlight = None
        list_item.clicker = None

    def _bind_factory(self,
                      list_item_factory: Gtk.SignalListItemFactory,
                      list_item:         Gtk.ListItem,
                      ) ->               None:
        """"""
        container = list_item.get_child()
        item_data = list_item.get_item()

        is_separator = item_data.is_separator
        list_item.set_focusable(not is_separator)
        list_item.set_selectable(not is_separator)
        list_item.set_activatable(not is_separator)
        list_item.content.set_visible(not is_separator)
        list_item.separator.set_visible(is_separator)

        if is_separator:
            return

        list_item.label.set_label(item_data.label)
        list_item.shortcut.set_visible(False)

        list_item.highlight = item_data.bind_property(source_property = 'label',
                                                      target          = list_item.label,
                                                      target_property = 'label',
                                                      flags           = GObject.BindingFlags.SYNC_CREATE)

        def on_click(gesture: Gtk.GestureClick,
                     n_press: int,
                     x:       float,
                     y:       float,
                     ) ->     None:
            """"""
            _, position = self.ListStore.find(item_data)
            self.Selection.set_selected(position)
            self._on_entry_activated(self.Entry)

        list_item.clicker = Gtk.GestureClick()
        list_item.clicker.connect('released', on_click)
        container.add_controller(list_item.clicker)

        if len(item_data.shortcuts) > 0:
            shortcut_string = item_data.shortcuts[0]
            is_parsed, accel_key, accel_mods = Gtk.accelerator_parse(shortcut_string)

            if is_parsed:
                label = Gtk.accelerator_get_label(accel_key, accel_mods)
                list_item.shortcut.set_label(label)
                list_item.shortcut.set_visible(True)

    def _unbind_factory(self,
                        list_item_factory: Gtk.SignalListItemFactory,
                        list_item:         Gtk.ListItem,
                        ) ->               None:
        """"""
        container = list_item.get_child()

        list_item.highlight.unbind()
        container.remove_controller(list_item.clicker)

    @Gtk.Template.Callback()
    def _on_entry_activated(self,
                            entry: Gtk.Entry,
                            ) ->   None:
        """"""
        window = self.get_root()

        selected_item = self.Selection.get_selected_item()

        if not selected_item:
            return

        editor = window.get_selected_editor()
        editor.activate_action(selected_item.action_name,
                               selected_item.action_args)

        window.activate_action('win.focus-editor')

    @Gtk.Template.Callback()
    def _on_entry_changed(self,
                          entry: Gtk.Entry,
                          ) ->   None:
        """"""
        query = entry.get_text()

        if query == '':
            # Reset all the labels
            for iidx in range(self.ListStore.get_n_items()):
                current_item = self.ListStore.get_item(iidx)
                current_item.label = current_item.title

            self.ScrolledWindow.get_vscrollbar().set_visible(True)
            self.ScrolledWindow.set_visible(True)

            # Show all items if the query is empty
            self.Selection.set_model(self.ListStore)
            self.ListView.scroll_to(0, Gtk.ListScrollFlags.SELECT, None)

            self._refresh_ui()

            return

        new_list_store = Gio.ListStore()

        # Get all the items that match the query
        for iidx in range(self.ListStore.get_n_items()):
            current_item = self.ListStore.get_item(iidx)

            # Skip recent and separator items
            if current_item.is_recent_item or current_item.is_separator:
                continue

            # Get the highlighted string for the current item
            highlighted_title = self._get_highlighted_string(query, current_item.title)

            # If a match was found, update the item with the highlighted title
            # and append it to the new list store.
            if highlighted_title is not None:
                current_item.label = highlighted_title
                new_list_store.append(current_item)

        self.Selection.set_model(new_list_store)

        self._refresh_ui()

    def _refresh_ui(self) -> None:
        """"""
        list_store = self.Selection.get_model()
        n_list_items = list_store.get_n_items()

        if n_list_items > 3:
            self.ScrolledWindow.get_vscrollbar().set_visible(True)
            self.ScrolledWindow.set_policy(hscrollbar_policy = Gtk.PolicyType.AUTOMATIC,
                                           vscrollbar_policy = Gtk.PolicyType.AUTOMATIC)
        else:
            self.ScrolledWindow.get_vscrollbar().set_visible(False)
            self.ScrolledWindow.set_policy(hscrollbar_policy = Gtk.PolicyType.AUTOMATIC,
                                           vscrollbar_policy = Gtk.PolicyType.NEVER)

        if n_list_items > 0:
            self.ListView.scroll_to(0, Gtk.ListScrollFlags.SELECT, None)
            self.ScrolledWindow.set_visible(True)
        else:
            self.ScrolledWindow.set_visible(False)

    @Gtk.Template.Callback()
    def _on_entry_deleted(self,
                          entry:     Gtk.Entry,
                          start_pos: int,
                          end_pos:   int,
                          ) ->       None:
        """"""
        self._on_entry_changed(entry)

    def _on_key_pressed(self,
                        event:   Gtk.EventControllerKey,
                        keyval:  int,
                        keycode: int,
                        state:   Gdk.ModifierType,
                        ) ->     bool:
        """"""
        if keyval == Gdk.KEY_Escape:
            self.popdown()
            return True

        # Map tab keys to arrow keys
        if keyval in {Gdk.KEY_Tab, Gdk.KEY_ISO_Left_Tab}:
            keyval = Gdk.KEY_Down
            if state in {Gdk.ModifierType.SHIFT_MASK}:
                keyval = Gdk.KEY_Up

        # Cycle through the commands and keep the focus on the entry box
        if keyval in {Gdk.KEY_Up, Gdk.KEY_Down}:
            n_items = self.Selection.get_model().get_n_items()

            position = self.Selection.get_selected()
            position += 1 if keyval == Gdk.KEY_Down else -1
            position %= n_items

            # Skip the separator item
            selected_item = self.Selection.get_selected_item()
            if selected_item.is_separator:
                if keyval == Gdk.KEY_Up:
                    position -= 1
                if keyval == Gdk.KEY_Down:
                    position += 1
                position %= n_items

            self.ListView.scroll_to(position, Gtk.ListScrollFlags.SELECT, None)

            return True

        return False

    @Gtk.Template.Callback()
    def _on_list_view_activated(self,
                                list_view: Gtk.ListView,
                                position:  int,
                                ) ->       None:
        """"""
        model = list_view.get_model()
        model.set_selected(position)
        self._on_entry_activated(self.Entry)

    def _find_subsequence_indices(self,
                                  query:  str,
                                  target: str,
                                  ) ->    list[int]:
        """
        Finds the indices of the characters in `target` that form the `query` subsequence.

        Returns a list of indices if found, otherwise None.
        """
        qlower = query.lower()
        tlower = target.lower()

        query_index = 0
        target_index = 0
        matched_indices = []

        while query_index < len(qlower) and target_index < len(tlower):
            if qlower[query_index] == tlower[target_index]:
                matched_indices.append(target_index)
                query_index += 1
            target_index += 1

        # If we matched every character in the query, return the indices
        if query_index == len(qlower):
            return matched_indices
        return None

    def _get_highlighted_string(self,
                                query:  str,
                                target: str,
                                ) ->    str:
        """
        Generates an HTML string with `<span>` tags around the matched subsequence.

        Returns the highlighted string if a match is found, otherwise None.
        """
        from html import unescape

        from .utils import get_standalone_accent_color

        # Unescape the target string for the subsequence search
        plain_target = unescape(target)
        matched_indices = self._find_subsequence_indices(query, plain_target)

        if matched_indices is None:
            return None

        is_matched_at_index = {idx for idx in matched_indices}

        parts = []
        orig_target_cursor = 0
        plain_cursor = 0

        color = get_standalone_accent_color()

        # Iterate through the original target string
        while orig_target_cursor < len(target):
            is_bold = plain_cursor in is_matched_at_index

            # Determine if we need to start a new bold tag
            if is_bold and (plain_cursor == 0 or
                            plain_cursor - 1 not in is_matched_at_index):
                parts.append(f'<span color="{color}" weight="bold">')

            # Check for HTML entities in the original string
            if target[orig_target_cursor] == '&':
                end_entity_index = target.find(';', orig_target_cursor)
                if end_entity_index != -1:
                    entity_str = target[orig_target_cursor:end_entity_index+1]
                    parts.append(entity_str)
                    orig_target_cursor = end_entity_index + 1
                # Malformed entity, treat '&' as a regular character
                else:
                    parts.append('&')
                    orig_target_cursor += 1
            else:
                # Handle regular characters
                parts.append(target[orig_target_cursor])
                orig_target_cursor += 1

            # Determine if we need to close the bold tag
            if is_bold and (plain_cursor + 1 not in is_matched_at_index):
                parts.append('</span>')

            plain_cursor += 1

        return ''.join(parts)
