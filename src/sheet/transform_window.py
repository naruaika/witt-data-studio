# transform_window.py
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
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Pango
from sys import float_info
import json

from ..core.utils import isiterable
from ..core.utils import toboolean

class SheetOperationArg(GObject.Object):

    __gtype_name__ = 'SheetOperationArg'

    value = GObject.Property(type = str, default = '')
    stype = GObject.Property(type = str, default = 'str')


@Gtk.Template(resource_path = '/com/macipra/witt/sheet/transform_window.ui')
class SheetTransformWindow(Adw.Window):

    __gtype_name__ = 'SheetTransformWindow'

    WindowTitle      = Gtk.Template.Child()
    PreferencesPage  = Gtk.Template.Child()
    ContentContainer = Gtk.Template.Child()
    OptionsContainer = Gtk.Template.Child()
    ApplyButton      = Gtk.Template.Child()

    def __init__(self,
                 title:         str,
                 subtitle:      str,
                 layout:        list[tuple],
                 callback:      callable,
                 transient_for: Gtk.Window,
                 application:   Gtk.Application,
                 **kwargs:      dict,
                 ) ->           None:
        """"""
        super().__init__(transient_for = transient_for,
                         application   = application)

        self.set_title(title)
        self.WindowTitle.set_title(title)
        self.WindowTitle.set_subtitle(subtitle)

        # Disable scroll to focus behavior of the Gtk.Viewport
        scrolled_window = self.PreferencesPage.get_first_child()
        viewport = scrolled_window.get_first_child()
        viewport.set_scroll_to_focus(False)

        # Make the window resize its height dynamically
        scrolled_window.set_max_content_height(452)
        scrolled_window.set_propagate_natural_height(True)

        key_event_controller = Gtk.EventControllerKey()
        key_event_controller.connect('key-pressed', self._on_key_pressed)
        self.add_controller(key_event_controller)

        self.callback = callback
        self.kwargs   = kwargs
        self.options  = {}
        self.op_args  = []

        n_content = 0
        n_options = 0

        for item in layout:
            operation_arg = SheetOperationArg()
            self.op_args.append(operation_arg)

            title, dtype = item[0], item[1]
            description = None
            contents = []
            defaults = []

            if isiterable(title):
                title = item[0][0]
                description = item[0][1]
            if len(item) > 2:
                contents = item[2]
            if len(item) > 3:
                defaults = item[3]

            match dtype:
                case 'combo':
                    self._create_combo_row(title, description, contents, operation_arg)
                    n_content += 1
                case 'entry':
                    self._create_entry_row(title, operation_arg)
                    n_content += 1
                case 'spin':
                    self._create_spin_row(title, description, operation_arg)
                    n_content += 1
                case 'switch':
                    self._create_switch_row(title, description, operation_arg)
                    n_content += 1
                case 'list-check':
                    self._create_list_check(title, description, contents, defaults, operation_arg)
                case 'list-entry':
                    self._create_list_entry(title, contents, operation_arg)
                case 'list-item':
                    self._create_list_item(title, contents, operation_arg)
                case 'list-switch':
                    self._create_list_switch(contents, operation_arg)

        if 'new_column' in self.kwargs:
            self._create_new_column_row()
            n_options += 1
        if 'new_sheet' in self.kwargs:
            self._create_new_sheet_row()
            n_options += 1

        # Remove or re-position to the end
        self.PreferencesPage.remove(self.OptionsContainer)
        if n_content == 0:
            self.ContentContainer.unparent()
        if n_options > 0:
            self.PreferencesPage.add(self.OptionsContainer)

        # We set the maximum content height previously to prevent
        # the window from filling the entire user screen's height.
        # But we don't want to prevent from manually resizing the
        # window to any size, so we reset the property here.
        GLib.idle_add(scrolled_window.set_max_content_height, -1)

    def _create_combo_row(self,
                          title:       str,
                          description: str,
                          options:     list[str],
                          ops_arg:     SheetOperationArg,
                          ) ->         None:
        """"""
        combo = Adw.ComboRow(title = title)
        if description not in {'', None}:
            combo.set_subtitle(description)
        combo_model = Gtk.StringList()
        for option in options:
            combo_model.append(option)
        combo.set_model(combo_model)
        combo.bind_property(source_property = 'selected-item',
                            target          = ops_arg,
                            target_property = 'value',
                            flags           = GObject.BindingFlags.SYNC_CREATE,
                            transform_to    = lambda _, val: val.get_string())
        self.ContentContainer.add(combo)

    def _create_entry_row(self,
                          title:   str,
                          ops_arg: SheetOperationArg,
                          ) ->     None:
        """"""
        entry = Adw.EntryRow(title = title)
        entry.bind_property('text', ops_arg, 'value', GObject.BindingFlags.SYNC_CREATE)
        entry.connect('entry-activated', self._on_input_activated)
        self.ContentContainer.add(entry)

    def _create_spin_row(self,
                         title:       str,
                         description: str,
                         ops_arg:     SheetOperationArg,
                         ) ->         None:
        """"""
        spin = Adw.SpinRow(title = title)
        if description not in {'', None}:
            spin.set_subtitle(description)
        spin.set_range(float_info.min, float_info.max)
        spin.get_adjustment().set_page_increment(5)
        spin.get_adjustment().set_step_increment(1)
        spin.bind_property('text', ops_arg, 'value', GObject.BindingFlags.SYNC_CREATE)
        self.ContentContainer.add(spin)
        ops_arg.stype = 'int'

    def _create_switch_row(self,
                           title:       str,
                           description: str,
                           ops_arg:     SheetOperationArg,
                           ) ->         None:
        """"""
        switch = Adw.SwitchRow(title = title)
        if description not in {'', None}:
            switch.set_subtitle(description)
        switch.bind_property('active', ops_arg, 'value', GObject.BindingFlags.SYNC_CREATE)
        self.ContentContainer.add(switch)
        ops_arg.stype = 'bool'

    def _create_list_check(self,
                           title:       str,
                           description: str,
                           options:     list[str],
                           defaults:    list[str],
                           ops_arg:     SheetOperationArg,
                           ) ->         None:
        """"""
        def on_check_toggled(button: Gtk.CheckButton,
                             value:  str,
                             ) ->    None:
            """"""
            args = json.loads(ops_arg.value) \
                   if ops_arg.value else []
            args.append(value) if button.get_active() \
                               else args.remove(value)
            ops_arg.value = json.dumps(args)

        row = Adw.PreferencesRow(activatable = False)

        box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        row.set_child(box)

        box.get_parent().set_activatable(False)

        subbox = Gtk.Box(orientation   = Gtk.Orientation.VERTICAL,
                         margin_top    = 6,
                         margin_bottom = 6,
                         margin_start  = 10,
                         margin_end    = 10)
        subbox.add_css_class('title')
        box.append(subbox)

        label_title = Gtk.Label(halign    = Gtk.Align.START,
                                ellipsize = Pango.EllipsizeMode.END,
                                label     = title)
        label_title.add_css_class('title')
        subbox.append(label_title)

        if description not in {'', None}:
            label_description = Gtk.Label(xalign    = 0.0,
                                          wrap      = True,
                                          wrap_mode = Pango.WrapMode.WORD,
                                          label     = description)
            label_description.add_css_class('subtitle')
            subbox.append(label_description)

        list_view = Gtk.FlowBox(margin_top     = 6,
                                margin_bottom  = 6,
                                margin_start   = 4,
                                margin_end     = 4,
                                column_spacing = 4,
                                row_spacing    = 4,
                                selection_mode = Gtk.SelectionMode.NONE,
                                homogeneous    = True)
        list_view.add_css_class('navigation-sidebar')
        box.append(list_view)

        for option in options:
            label = Gtk.Label(halign    = Gtk.Align.START,
                              valign    = Gtk.Align.CENTER,
                              hexpand   = True,
                              ellipsize = Pango.EllipsizeMode.MIDDLE,
                              label     = option)
            check_button = Gtk.CheckButton(child         = label,
                                           margin_top    = 2,
                                           margin_bottom = 2,
                                           margin_start  = 2,
                                           margin_end    = 2,
                                           active        = option in defaults)
            check_button.connect('toggled', on_check_toggled, option)
            list_view.append(check_button)

        ops_arg.value = json.dumps(defaults)

        if title in {'', None}:
            subbox.set_visible(False)

        group = Adw.PreferencesGroup()
        box = group.get_first_child()
        box = box.get_last_child()
        list_box = box.get_first_child()
        list_box.remove_css_class('boxed-list')
        list_box.add_css_class('boxed-list-separate')
        self.PreferencesPage.add(group)
        group.add(row)

        ops_arg.stype = 'strv'

    def _create_list_entry(self,
                           title:      str,
                           contents:   list,
                           ops_arg:    SheetOperationArg,
                           group:      Adw.PreferencesGroup = None,
                           add_button: Adw.ButtonRow        = None,
                           ) ->        None:
        """"""
        # Initialize the operation arguments with an empty string
        # where each argument correspond to a child input widget.
        ops_arg.value = json.dumps([''] * (1 + len(contents)))

        if create_new_group := group is None:
            group = Adw.PreferencesGroup()
            box = group.get_first_child()
            box = box.get_last_child()
            list_box = box.get_first_child()
            list_box.remove_css_class('boxed-list')
            list_box.add_css_class('boxed-list-separate')
            self.PreferencesPage.add(group)

        def on_entry_changed(widget: Gtk.Widget,
                             pspec:  GObject.ParamSpec,
                             ) ->    None:
            """"""
            arg = ops_arg.value
            args = json.loads(arg) if arg else []
            args[0] = widget.get_text()
            ops_arg.value = json.dumps(args)

        entry = Adw.EntryRow(title = title)
        entry.add_css_class('list-item-entry')
        entry.connect('notify::text', on_entry_changed)
        group.add(entry)

        box = entry.get_first_child()
        box.set_orientation(Gtk.Orientation.VERTICAL)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_spacing(10)

        prefixes = box.get_first_child()
        editable = prefixes.get_next_sibling()
        separator = Gtk.Separator(orientation = Gtk.Orientation.VERTICAL)
        box.insert_child_after(separator, editable)

        suffix = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL,
                         spacing     = 6,
                         homogeneous = True,
                         visible     = len(contents) > 0)
        entry.add_suffix(suffix)

        chindex = 1 # the first index (or zero) is already taken
                    # by the entry widget, so we start from one.
        for dtype, options in contents:
            match dtype:
                case 'dropdown':
                    self._create_child_dropdown(options, suffix, chindex, ops_arg)
            chindex += 1

        def on_delete_button_clicked(button: Gtk.Button) -> None:
            """"""
            group.remove(entry)
            ops_index = self.op_args.index(ops_arg)
            del self.op_args[ops_index]

        delete_button = Gtk.Button(valign    = Gtk.Align.CENTER,
                                   icon_name = 'user-trash-symbolic')
        delete_button.add_css_class('flat')
        delete_button.add_css_class('circular')
        delete_button.connect('clicked', on_delete_button_clicked)
        entry.add_suffix(delete_button)

        if not create_new_group:
            entry.grab_focus()

        def on_add_button_clicked(button: Gtk.Button) -> None:
            """"""
            new_ops_arg = SheetOperationArg()
            self.op_args.append(new_ops_arg)
            self._create_list_entry(title, contents, new_ops_arg, group, button)

            def do_scroll() -> None:
                """"""
                scrolled_window = self.PreferencesPage.get_first_child()
                viewport = scrolled_window.get_first_child()
                vadjustment = viewport.get_vadjustment()
                vadjustment.set_value(vadjustment.get_upper())
            GLib.idle_add(do_scroll)

        if create_new_group:
            add_button = Adw.ButtonRow(title           = f'{_('Add')} {title}',
                                       start_icon_name = 'list-add-symbolic')
            add_button.connect('activated', on_add_button_clicked)
            group.add(add_button)
        else:
            group.remove(add_button)
            group.add(add_button)
            # Re-position to the end

        ops_arg.stype = 'strv'

    def _create_list_item(self,
                          title:      str,
                          contents:   list,
                          ops_arg:    SheetOperationArg,
                          group:      Adw.PreferencesGroup = None,
                          add_button: Adw.ButtonRow        = None,
                          ) ->        None:
        """"""
        # Initialize the operation arguments with an empty string
        # where each argument correspond to a child input widget.
        ops_arg.value = json.dumps([''] * len(contents))

        if create_new_group := group is None:
            group = Adw.PreferencesGroup()
            box = group.get_first_child()
            box = box.get_last_child()
            list_box = box.get_first_child()
            list_box.remove_css_class('boxed-list')
            list_box.add_css_class('boxed-list-separate')
            self.PreferencesPage.add(group)

        action = Adw.ActionRow()
        group.add(action)

        box = action.get_first_child()
        suffixes = box.get_last_child()
        title_box = suffixes.get_prev_sibling()
        title_box.set_visible(False)

        suffix = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL,
                         spacing     = 6,
                         homogeneous = True)
        action.add_suffix(suffix)

        chindex = 0
        for dtype, options in contents:
            match dtype:
                case 'dropdown':
                    self._create_child_dropdown(options, suffix, chindex, ops_arg)
            chindex += 1

        def on_delete_button_clicked(button: Gtk.Button) -> None:
            """"""
            group.remove(action)
            ops_index = self.op_args.index(ops_arg)
            del self.op_args[ops_index]

        delete_button = Gtk.Button(valign    = Gtk.Align.CENTER,
                                   icon_name = 'user-trash-symbolic')
        delete_button.add_css_class('flat')
        delete_button.add_css_class('circular')
        delete_button.connect('clicked', on_delete_button_clicked)
        action.add_suffix(delete_button)

        if not create_new_group:
            suffix.get_first_child().grab_focus()

        def on_add_button_clicked(button: Gtk.Button) -> None:
            """"""
            new_ops_arg = SheetOperationArg()
            self.op_args.append(new_ops_arg)
            self._create_list_item(title, contents, new_ops_arg, group, button)

            def do_scroll() -> None:
                """"""
                scrolled_window = self.PreferencesPage.get_first_child()
                viewport = scrolled_window.get_first_child()
                vadjustment = viewport.get_vadjustment()
                vadjustment.set_value(vadjustment.get_upper())
            GLib.idle_add(do_scroll)

        if create_new_group:
            add_button = Adw.ButtonRow(title           = f'{_('Add')} {title}',
                                       start_icon_name = 'list-add-symbolic')
            add_button.connect('activated', on_add_button_clicked)
            group.add(add_button)
        else:
            group.remove(add_button)
            group.add(add_button)
            # Re-position to the end

        ops_arg.stype = 'strv'

    def _create_list_switch(self,
                            options: list[str],
                            ops_arg: SheetOperationArg,
                            ) ->     None:
        """"""
        group = Adw.PreferencesGroup()
        box = group.get_first_child()
        box = box.get_last_child()
        list_box = box.get_first_child()
        list_box.remove_css_class('boxed-list')
        list_box.add_css_class('boxed-list-separate')
        self.PreferencesPage.add(group)

        def on_switch_activated(switch: Adw.SwitchRow,
                                param_spec: GObject.ParamSpec,
                                value:  str,
                                ) ->    None:
            """"""
            args = json.loads(ops_arg.value) \
                   if ops_arg.value else []
            args.append(value) if switch.get_active() \
                               else args.remove(value)
            ops_arg.value = json.dumps(args)

        for option in options:
            switch = Adw.SwitchRow(title = option)
            switch.connect('notify::active', on_switch_activated, option)
            group.add(switch)

        ops_arg.stype = 'strv'

    def _create_child_dropdown(self,
                               options: list,
                               parent:  Gtk.Widget,
                               chindex: int,
                               ops_arg: SheetOperationArg,
                               ) ->     None:
        """"""
        dropdown = Gtk.DropDown(hexpand = True,
                                valign  = Gtk.Align.CENTER)

        button = dropdown.get_first_child()
        button.add_css_class('flat')

        def setup_factory_dropdown(list_item_factory: Gtk.SignalListItemFactory,
                                   list_item:         Gtk.ListItem,
                                   ) ->               None:
            """"""
            box = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL,
                          hexpand     = True)
            list_item.set_child(box)

            label = Gtk.Label()
            box.append(label)

            image = Gtk.Image(opacity = 0)
            image.set_from_icon_name('object-select-symbolic')
            box.append(image)

            list_item.label = label
            list_item.image = image
            list_item.bind_item = None

        def bind_factory_dropdown(list_item_factory: Gtk.SignalListItemFactory,
                                  list_item:         Gtk.ListItem,
                                  ) ->               None:
            """"""
            item_data = list_item.get_item()
            label = item_data.get_string()

            def on_list_item_selected(*args) -> None:
                """"""
                is_selected = list_item.get_selected()
                list_item.image.set_opacity(is_selected)
                if not is_selected:
                    return
                arg = ops_arg.value
                args = json.loads(arg) if arg else []
                args[chindex] = label
                ops_arg.value = json.dumps(args)

            list_item.label.set_label(label)

            if list_item.bind_item is not None:
                list_item.disconnect(list_item.bind_item)
                # TODO: do this in unbind function callback

            list_item.bind_item = dropdown.connect('notify::selected-item', on_list_item_selected)
            on_list_item_selected() # setup default selected list item

        def teardown_factory_dropdown(list_item_factory: Gtk.SignalListItemFactory,
                                      list_item:         Gtk.ListItem,
                                      ) ->               None:
            """"""
            list_item.label = None
            list_item.image = None
            list_item.bind_item = None

        dropdown_model = Gtk.StringList()
        for option in options:
            dropdown_model.append(option)
        dropdown.set_model(dropdown_model)

        dropdown_list_factory = Gtk.SignalListItemFactory()
        dropdown_list_factory.connect('setup', setup_factory_dropdown)
        dropdown_list_factory.connect('bind', bind_factory_dropdown)
        dropdown_list_factory.connect('teardown', teardown_factory_dropdown)
        dropdown.set_list_factory(dropdown_list_factory)

        dropdown_factory = Gtk.BuilderListItemFactory.new_from_bytes(None, GLib.Bytes.new(bytes(
"""
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <template class="GtkListItem">
    <property name="child">
      <object class="GtkLabel">
        <property name="halign">start</property>
        <property name="hexpand">true</property>
        <property name="ellipsize">end</property>
        <binding name="label">
          <lookup name="string" type="GtkStringObject">
            <lookup name="item">GtkListItem</lookup>
          </lookup>
        </binding>
      </object>
    </property>
  </template>
</interface>
""", 'utf-8')))
        dropdown.set_factory(dropdown_factory)

        parent.append(dropdown)

    def _create_new_column_row(self):
        """"""
        self.options['new_column'] = Adw.ExpanderRow(title              = _('To New Column'),
                                                     enable_expansion   = self.kwargs['new_column'],
                                                     show_enable_switch = True,
                                                     expanded           = True)
        self.OptionsContainer.add(self.options['new_column'])

        self.options['column_rename'] = Adw.EntryRow(title = _('Name'))
        self.options['column_prefix'] = Adw.EntryRow(title = _('Prefix'))
        self.options['column_suffix'] = Adw.EntryRow(title = _('Suffix'))

        self.options['new_column'].add_row(self.options['column_rename'])
        self.options['new_column'].add_row(self.options['column_prefix'])
        self.options['new_column'].add_row(self.options['column_suffix'])

    def _create_new_sheet_row(self):
        """"""
        self.options['new_sheet'] = Adw.SwitchRow(title  = _('To New Sheet'),
                                                  active = self.kwargs['new_sheet'])
        self.OptionsContainer.add(self.options['new_sheet'])

    def _get_callback_args(self) -> list:
        """"""
        args = []

        for operation_arg in self.op_args:
            arg = operation_arg.value

            # Cast the argument value if needed
            if operation_arg.stype == 'int':
                arg = int(arg if arg.isnumeric() else 0)
            if operation_arg.stype == 'bool':
                arg = toboolean(arg)
            if operation_arg.stype == 'strv':
                arg = json.loads(arg) if arg else []

            args.append(arg)

        return args

    @Gtk.Template.Callback()
    def _on_apply_button_clicked(self,
                                 button: Gtk.Button,
                                 ) ->    None:
        """"""
        if 'new_column' in self.kwargs:
            self.kwargs['new_column']    = self.options['new_column'].get_enable_expansion()
            self.kwargs['column_rename'] = self.options['column_rename'].get_text()
            self.kwargs['column_prefix'] = self.options['column_prefix'].get_text()
            self.kwargs['column_suffix'] = self.options['column_suffix'].get_text()

        if 'new_sheet' in self.kwargs:
            self.kwargs['new_sheet'] = self.options['new_sheet'].get_active()

        self.close() # close first to properly handle the focus
        self.callback(self._get_callback_args(), **self.kwargs)

    def _on_input_activated(self,
                            widget: Gtk.Widget,
                            ) ->    None:
        """"""
        self._on_apply_button_clicked(self.ApplyButton)

    def _on_key_pressed(self,
                        event:   Gtk.EventControllerKey,
                        keyval:  int,
                        keycode: int,
                        state:   Gdk.ModifierType,
                        ) ->     bool:
        """"""
        if keyval == Gdk.KEY_Escape:
            self.close()
            return False
