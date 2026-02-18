# editor.py
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

from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gtk

@Gtk.Template(resource_path = '/com/wittara/studio/chart/editor.ui')
class ChartEditor(Gtk.Overlay):

    __gtype_name__ = 'ChartEditor'

    HorizontalScrollbar = Gtk.Template.Child()
    VerticalScrollbar   = Gtk.Template.Child()

    ICON_NAME     = 'profit-symbolic'
    ACTION_PREFIX = 'chart'

    title = GObject.Property(type = str, default = _('Chart'))

    def __init__(self,
                 title:   str  = _('Chart'),
                 configs: dict = {},
                 ) ->     None:
        """"""
        super().__init__()

        self.title = title

        self.configs = {}
        self.configs.update(configs)

        self.Canvas = ChartCanvas()
        # self.Canvas.set_halign(Gtk.Align.START)
        # self.Canvas.set_valign(Gtk.Align.START)
        # self.Canvas.set_size_request(512, 512)
        self.set_child(self.Canvas)

        self.display  = ChartDisplay()
        self.document = ChartDocument()
        self.view     = ChartView(self.Canvas,
                                  self.HorizontalScrollbar,
                                  self.VerticalScrollbar,
                                  self.document,
                                  self.display)

        self._setup_actions()
        self._setup_commands()

    def setup(self) -> None:
        """"""
        pass

    def grab_focus(self) -> None:
        """"""
        self.Canvas.set_focusable(True)
        self.Canvas.grab_focus()

    def refresh_ui(self) -> None:
        """"""
        pass

    def cleanup(self) -> None:
        """"""
        pass

    def queue_draw(self) -> None:
        """"""
        self.Canvas.queue_draw()

    def queue_resize(self) -> None:
        """"""
        Gtk.Widget.queue_resize(self)

    def get_command_list(self) -> list[dict]:
        """"""
        from ..core.context_evaluator import Evaluator

        variables = {}

        def isrelevant(context: str) -> bool:
            """"""
            if context is None:
                return True
            try:
                return Evaluator(variables).evaluate(context)
            except:
                return False

        command_list = []
        for command in self._command_list:
            if not isrelevant(command['context']):
                continue
            command_list.append(command)

        return command_list

    def _setup_actions(self) -> None:
        """"""
        group = Gio.SimpleActionGroup.new()
        self.insert_action_group(self.ACTION_PREFIX, group)

        controller = Gtk.ShortcutController()
        self.add_controller(controller)

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
                string_action = f'action({self.ACTION_PREFIX}.{name})'
                action = Gtk.ShortcutAction.parse_string(string_action)
                shortcut = Gtk.Shortcut.new(trigger, action)
                controller.add_shortcut(shortcut)

        pass

    def _setup_commands(self) -> None:
        """"""
        self._command_list = []

        def create_command(action_name: str,
                           title:       str,
                           name:        str          = None,
                           action_args: GLib.Variant = None,
                           shortcuts:   list[str]    = [],
                           context:     str          = None,
                           prefix:      str          = 'chart',
                           ) ->         None:
            """"""
            self._command_list.append({
                'name':        name or action_name,
                'title':       title,
                'shortcuts':   shortcuts,
                'action-name': f'{prefix}.{action_name}',
                'action-args': action_args,
                'context':     context,
            })

        pass

from .canvas import ChartCanvas
from .display import ChartDisplay
from .document import ChartDocument
from .view import ChartView
