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
from typing import Any
import json

from ..core.utils import isiterable
from ..core.utils import toboolean

class SheetTransformOpsArg(GObject.Object):

    __gtype_name__ = 'SheetTransformOpsArg'

    value = GObject.Property(type = str, default = '')
    stype = GObject.Property(type = str, default = 'str')


@Gtk.Template(resource_path = '/com/wittara/studio/sheet/transform_window.ui')
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
        self.WindowTitle.set_title(_('Transform'))

        # Disable scroll to focus behavior of the Gtk.Viewport
        scrolled_window = self.PreferencesPage.get_first_child()
        viewport = scrolled_window.get_first_child()
        viewport.set_scroll_to_focus(False)

        # Make the window resize its height dynamically
        scrolled_window.set_max_content_height(640)
        scrolled_window.set_propagate_natural_height(True)

        self.callback = callback
        self.kwargs   = kwargs
        self.options  = {}
        self.op_args  = []

        self.n_content = 0
        self.n_options = 0

        self.is_dynamic = False

        for item in layout:
            self._create_widget(item)

        if 'new_column' in self.kwargs:
            self._create_new_column_row()
            self.n_options += 1
        if 'new_sheet' in self.kwargs:
            self._create_new_sheet_row()
            self.n_options += 1

        # Remove or re-position to the end
        self.PreferencesPage.remove(self.OptionsContainer)
        if self.n_content == 0:
            self.ContentContainer.unparent()
        if self.n_options > 0:
            self.PreferencesPage.add(self.OptionsContainer)

        if self.is_dynamic:
            scrolled_window.set_min_content_height(362)

        # We set the maximum content height previously to prevent
        # the window from filling the entire user screen's height
        # but we don't want to prevent from manually resizing the
        # window to any size, so we reset the property here.
        GLib.idle_add(scrolled_window.set_min_content_height, -1)
        GLib.idle_add(scrolled_window.set_max_content_height, -1)

        # We set the window title after a delay so that the window
        # when displayed doesn't try to resize to fit the title in
        # case the title is too long
        GLib.idle_add(self.WindowTitle.set_title, title)
        GLib.idle_add(self.WindowTitle.set_subtitle, subtitle)

        controller = Gtk.EventControllerKey()
        controller.connect('key-pressed', self._on_key_pressed)
        self.add_controller(controller)

        self.ApplyButton.grab_focus()

    def _create_widget(self,
                       item: Any,
                       ) ->  None:
        """"""
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

        custom = dtype.endswith(':custom')
        dtype = dtype.removesuffix(':custom')

        indexed = dtype.endswith(':indexed')
        dtype = dtype.removesuffix(':indexed')

        if dtype != 'group':
            ops_arg = SheetTransformOpsArg()
            self.op_args.append(ops_arg)

        match dtype:
            case 'group':
                main_group = self.ContentContainer

                group = Adw.PreferencesGroup()
                self.PreferencesPage.add(group)
                self.ContentContainer = group
                if title:
                    group.set_title(title)

                for i in contents:
                    self._create_widget(i)

                self.ContentContainer = main_group

            case 'combo':
                default = defaults[0] if defaults else None
                self._create_combo_row(title, description, contents, default, custom, ops_arg)
                self.n_content += 1

            case 'entry':
                default = contents if contents != [] else None
                self._create_entry_row(title, default, ops_arg)
                self.n_content += 1

            case 'spin':
                lower, upper, digits = contents if contents else (None, None, 0)
                self._create_spin_row(title, description, lower, upper, digits, ops_arg)
                self.n_content += 1

            case 'switch':
                self._create_switch_row(title, description, ops_arg)
                self.n_content += 1

            case 'list-check':
                self._create_list_check(title, description, contents, defaults, indexed, ops_arg)

            case 'list-entry':
                self._create_list_entry(title, contents, ops_arg)
                self.is_dynamic = True

            case 'list-item':
                self._create_list_item(title, contents, ops_arg)
                self.is_dynamic = True

            case 'list-switch':
                self._create_list_switch(contents, ops_arg)

    def _create_combo_row(self,
                          title:       str,
                          description: str,
                          options:     dict,
                          default:     str,
                          custom:      bool,
                          ops_arg:     SheetTransformOpsArg,
                          ) ->         None:
        """"""
        combo = Adw.ComboRow(title = title)

        if description not in {'', None}:
            combo.set_subtitle(description)

        if isinstance(options, list):
            options = {o: o for o in options}

        model = Gtk.StringList()
        for option in options.values():
            model.append(option)
        if custom:
            model.append(_('Custom'))
        combo.set_model(model)

        if custom:
            group = Adw.PreferencesGroup()
            self.PreferencesPage.add(group)
            group.add(combo)
        else:
            self.ContentContainer.add(combo)

        if custom:
            custom_ops_arg = SheetTransformOpsArg()
            entry = Adw.EntryRow(title = _('Custom'))
            group.add(entry)

            def custom_transform_to(binding: GObject.Binding,
                                    text:    str,
                                    ) ->     str:
                """"""
                position = combo.get_selected()
                if custom and position == len(options):
                    ops_arg.value = text
                    return text

            entry.bind_property(source_property = 'text',
                                target          = custom_ops_arg,
                                target_property = 'value',
                                flags           = GObject.BindingFlags.SYNC_CREATE,
                                transform_to    = custom_transform_to)

        def transform_to(binding:  GObject.Binding,
                         position: int,
                         ) ->      str:
            """"""
            if custom:
                entry.set_sensitive(False)
                if position == len(options):
                    entry.set_sensitive(True)
                    return custom_ops_arg.value
            return list(options.keys())[position]

        combo.bind_property(source_property = 'selected',
                            target          = ops_arg,
                            target_property = 'value',
                            flags           = GObject.BindingFlags.SYNC_CREATE,
                            transform_to    = transform_to)

        if default:
            selected = next((i for i, key in enumerate(options) if key == default), 0)
            combo.set_selected(selected)
        else:
            combo.set_selected(0)

    def _create_entry_row(self,
                          title:   str,
                          default: str,
                          ops_arg: SheetTransformOpsArg,
                          ) ->     None:
        """"""
        entry = Adw.EntryRow(title = title)
        entry.bind_property('text', ops_arg, 'value', GObject.BindingFlags.SYNC_CREATE)
        self.ContentContainer.add(entry)

        if default is not None:
            entry.set_text(str(default))

        if isinstance(default, (int, float)):
            entry.set_input_purpose(Gtk.InputPurpose.NUMBER)

            def on_changed(entry: Adw.EntryRow) -> None:
                """"""
                text = entry.get_text()
                try:
                    if isinstance(default, int):
                        int(text)
                    if isinstance(default, float):
                        float(text)
                except:
                    entry.add_css_class('warning')
                else:
                    entry.remove_css_class('warning')

            entry.connect('changed', on_changed)

    def _create_spin_row(self,
                         title:       str,
                         description: str,
                         lower:       int,
                         upper:       int,
                         digits:      int,
                         ops_arg:     SheetTransformOpsArg,
                         ) ->         None:
        """"""
        spin = Adw.SpinRow(title  = title,
                           digits = digits)
        if description not in {'', None}:
            spin.set_subtitle(description)
        lower = -GLib.MAXDOUBLE if lower is None else lower
        upper = +GLib.MAXDOUBLE if upper is None else upper
        spin.set_range(lower, upper)
        spin.get_adjustment().set_page_increment(5)
        spin.get_adjustment().set_step_increment(1)
        spin.bind_property('text', ops_arg, 'value', GObject.BindingFlags.SYNC_CREATE)
        self.ContentContainer.add(spin)
        ops_arg.stype = 'int' if digits == 0 else 'float'

    def _create_switch_row(self,
                           title:       str,
                           description: str,
                           ops_arg:     SheetTransformOpsArg,
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
                           indexed:     bool,
                           ops_arg:     SheetTransformOpsArg,
                           ) ->         None:
        """"""
        def on_check_toggled(button: Gtk.CheckButton,
                             value:  str,
                             ) ->    None:
            """"""
            if indexed:
                value = options.index(value)
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
            label_description = Gtk.Label(xalign     = 0.0,
                                          wrap       = True,
                                          wrap_mode  = Pango.WrapMode.WORD,
                                          label      = description,
                                          margin_top = 3)
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
                           title:    str,
                           contents: list,
                           ops_arg:  SheetTransformOpsArg,
                           ) ->      None:
        """"""
        group = Adw.PreferencesGroup()
        box = group.get_first_child()
        box = box.get_last_child()
        list_box = box.get_first_child()
        list_box.remove_css_class('boxed-list')
        list_box.add_css_class('boxed-list-separate')
        self.PreferencesPage.add(group)

        ops_arg.value = json.dumps([])
        ops_arg.stype = 'strv'

        mdata = []

        class ItemData():

            def __init__(self,
                         ops_arg: SheetTransformOpsArg,
                         mdata:   list,
                         idata:   list,
                         index:   int,
                         ) ->     None:
                """"""
                self.ops_arg = ops_arg
                self.mdata   = mdata
                self.idata   = idata
                self.index   = index

            def get_data(self) -> str:
                """"""
                return self.idata[self.index]

            def set_data(self,
                         value: str,
                         ) ->   None:
                """"""
                self.idata[self.index] = value
                self.ops_arg.value = json.dumps(self.mdata)

        def add_list_item() -> None:
            """"""
            action = Adw.ActionRow()
            action.add_css_class('custom-row')
            group.add(action)

            box = action.get_first_child()
            suffixes = box.get_last_child()
            title_box = suffixes.get_prev_sibling()
            title_box.set_visible(False)

            idata = []

            vbox = Gtk.Box(orientation   = Gtk.Orientation.VERTICAL,
                           spacing       = 6,
                           valign        = Gtk.Align.CENTER,
                           margin_top    = 8,
                           margin_bottom = 8)
            action.add_suffix(vbox)

            idata.append('')
            item_data = ItemData(ops_arg, mdata, idata, 0)
            entry = self._create_child_entry(item_data.get_data,
                                             item_data.set_data)
            vbox.append(entry)

            container = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL,
                                spacing     = 6,
                                homogeneous = True)
            vbox.append(container)

            for index, content in enumerate(contents):
                if isiterable(content):
                    dtype, options = content
                    if isinstance(options, list):
                        options = {o: o for o in options}
                        contents[index] = (dtype, options)
                else:
                    dtype = content

                match dtype:
                    case 'dropdown':
                        value = next(iter(options.keys()))
                        idata.append(value)
                    case 'entry':
                        idata.append('')
                    case _:
                        idata.append(None)

            mdata.append(idata)

            for index, content in enumerate(contents):
                if isiterable(content):
                    dtype, options = content
                else:
                    dtype = content

                item_data = ItemData(ops_arg, mdata, idata, index + 1)

                match dtype:
                    case 'dropdown':
                        dropdown = self._create_child_dropdown(item_data.get_data,
                                                               item_data.set_data,
                                                               options)
                        container.append(dropdown)

                    case 'entry':
                        entry = self._create_child_entry(item_data.get_data,
                                                         item_data.set_data)
                        container.append(entry)

            def on_delete_button_clicked(button: Gtk.Button) -> None:
                """"""
                group.remove(action)
                index = next(i for i, x in enumerate(mdata) if x is idata)
                del mdata[index]
                ops_arg.value = json.dumps(mdata)

            delete_button = Gtk.Button(icon_name     = 'user-trash-symbolic',
                                       margin_top    = 8,
                                       margin_bottom = 8)
            delete_button.add_css_class('circular')
            delete_button.add_css_class('error')
            delete_button.connect('clicked', on_delete_button_clicked)
            action.add_suffix(delete_button)

        add_button = Adw.ButtonRow(title           = f'{_('Add')} {title}',
                                   start_icon_name = 'list-add-symbolic')
        group.add(add_button)

        def on_add_button_clicked(button: Gtk.Button) -> None:
            """"""
            add_list_item()
            ops_arg.value = json.dumps(mdata)
            group.remove(add_button)
            group.add(add_button)

        add_button.connect('activated', on_add_button_clicked)

        add_button.activate()

    def _create_list_item(self,
                          title:    str,
                          contents: list,
                          ops_arg:  SheetTransformOpsArg,
                          ) ->      None:
        """"""
        group = Adw.PreferencesGroup()
        box = group.get_first_child()
        box = box.get_last_child()
        list_box = box.get_first_child()
        list_box.remove_css_class('boxed-list')
        list_box.add_css_class('boxed-list-separate')
        self.PreferencesPage.add(group)

        ops_arg.value = json.dumps([])
        ops_arg.stype = 'strv'

        mdata = []

        class ItemData():

            def __init__(self,
                         ops_arg: SheetTransformOpsArg,
                         mdata:   list,
                         idata:   list,
                         index:   int,
                         ) ->     None:
                """"""
                self.ops_arg = ops_arg
                self.mdata   = mdata
                self.idata   = idata
                self.index   = index

            def get_data(self) -> str:
                """"""
                return self.idata[self.index]

            def set_data(self,
                         value: str,
                         ) ->   None:
                """"""
                self.idata[self.index] = value
                self.ops_arg.value = json.dumps(self.mdata)

        def add_list_item() -> None:
            """"""
            action = Adw.ActionRow()
            action.add_css_class('custom-row')
            group.add(action)

            box = action.get_first_child()
            suffixes = box.get_last_child()
            title_box = suffixes.get_prev_sibling()
            title_box.set_visible(False)

            suffix = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL,
                             spacing     = 6,
                             homogeneous = True)
            action.add_suffix(suffix)

            idata = []

            for index, content in enumerate(contents):
                if isiterable(content):
                    dtype, options = content
                    if isinstance(options, list):
                        options = {o: o for o in options}
                        contents[index] = (dtype, options)
                else:
                    dtype = content

                match dtype:
                    case 'dropdown':
                        value = next(iter(options.keys()))
                        idata.append(value)
                    case 'entry':
                        idata.append('')
                    case _:
                        idata.append(None)

            mdata.append(idata)

            for index, content in enumerate(contents):
                if isiterable(content):
                    dtype, options = content
                else:
                    dtype = content

                item_data = ItemData(ops_arg, mdata, idata, index)

                match dtype:
                    case 'dropdown':
                        dropdown = self._create_child_dropdown(item_data.get_data,
                                                               item_data.set_data,
                                                               options)
                        suffix.append(dropdown)

                    case 'entry':
                        dropdown = self._create_child_entry(item_data.get_data,
                                                            item_data.set_data)
                        suffix.append(dropdown)

            def on_delete_button_clicked(button: Gtk.Button) -> None:
                """"""
                group.remove(action)
                index = next(i for i, x in enumerate(mdata) if x is idata)
                del mdata[index]
                ops_arg.value = json.dumps(mdata)

            delete_button = Gtk.Button(icon_name     = 'user-trash-symbolic',
                                       margin_top    = 8,
                                       margin_bottom = 8)
            delete_button.add_css_class('circular')
            delete_button.add_css_class('error')
            delete_button.connect('clicked', on_delete_button_clicked)
            action.add_suffix(delete_button)

        add_button = Adw.ButtonRow(title           = f'{_('Add')} {title}',
                                   start_icon_name = 'list-add-symbolic')
        group.add(add_button)

        def on_add_button_clicked(button: Gtk.Button) -> None:
            """"""
            add_list_item()
            ops_arg.value = json.dumps(mdata)
            group.remove(add_button)
            group.add(add_button)

        add_button.connect('activated', on_add_button_clicked)

        add_button.activate()

    def _create_list_switch(self,
                            options: list[str],
                            ops_arg: SheetTransformOpsArg,
                            ) ->     None:
        """"""
        group = Adw.PreferencesGroup()
        box = group.get_first_child()
        box = box.get_last_child()
        list_box = box.get_first_child()
        list_box.remove_css_class('boxed-list')
        list_box.add_css_class('boxed-list-separate')
        self.PreferencesPage.add(group)

        def on_switch_activated(switch:     Adw.SwitchRow,
                                param_spec: GObject.ParamSpec,
                                value:      str,
                                ) ->        None:
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
                               get_data: callable,
                               set_data: callable,
                               options:  dict,
                               ) ->      Gtk.DropDown:
        """"""
        dropdown = Gtk.DropDown(hexpand = True,
                                valign  = Gtk.Align.CENTER)

        def setup_factory(list_item_factory: Gtk.SignalListItemFactory,
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

        def bind_factory(list_item_factory: Gtk.SignalListItemFactory,
                         list_item:         Gtk.ListItem,
                         ) ->               None:
            """"""
            item_data = list_item.get_item()
            label = item_data.get_string()

            def do_select() -> bool:
                """"""
                is_selected = list_item.get_selected()
                list_item.image.set_opacity(is_selected)
                if is_selected:
                    dropdown.set_tooltip_text(label)
                return is_selected

            def on_selected(*args) -> None:
                """"""
                if do_select():
                    value = next((k for k, v in options.items() if v == label), None)
                    set_data(value)

            list_item.label.set_label(label)

            if list_item.bind_item:
                list_item.disconnect(list_item.bind_item)

            list_item.bind_item = dropdown.connect('notify::selected', on_selected)

            do_select()

        model = Gtk.StringList()
        for option in options.values():
            model.append(option)
        dropdown.set_model(model)

        list_factory = Gtk.SignalListItemFactory()
        list_factory.connect('setup', setup_factory)
        list_factory.connect('bind', bind_factory)
        dropdown.set_list_factory(list_factory)

        factory = Gtk.BuilderListItemFactory.new_from_bytes(None, GLib.Bytes.new(bytes(
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
        dropdown.set_factory(factory)

        selected = next((i for i, key in enumerate(options) if key == get_data()), 0)
        dropdown.set_selected(selected)

        return dropdown

    def _create_child_entry(self,
                            get_data: callable,
                            set_data: callable,
                            ) ->      Gtk.Entry:
        """"""
        entry = Gtk.Entry(hexpand          = True,
                          valign           = Gtk.Align.CENTER,
                          placeholder_text = f'[{_('Empty')}]')

        def on_text_changed(entry:      Gtk.Entry,
                            param_spec: GObject.ParamSpec,
                            ) ->        None:
            """"""
            set_data(entry.get_text())

        entry.connect('notify::text', on_text_changed)

        entry.set_text(get_data())

        return entry

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
            if operation_arg.stype == 'float':
                arg = float(arg if arg.isnumeric() else 0)
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
#       if keyval == Gdk.KEY_Escape:
#           self.close()
#           return Gdk.EVENT_STOP
        return Gdk.EVENT_PROPAGATE
