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

from copy import copy
from gi.repository import Adw
from gi.repository import Gdk
from gi.repository import GdkPixbuf
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Graphene
from gi.repository import Gtk
from numpy import array as narray
from scipy import spatial
from typing import TypeAlias
import cairo
import gc
import math

from .. import environment as env

Point2D:  TypeAlias = tuple[float, float]
Scalar2D: TypeAlias = tuple[Point2D, Point2D]

class NodeEditorGroup():

    def __init__(self) -> None:
        """"""
        self.nodes:  list['NodeFrame']       = []
        self.links:  list['NodeLink']        = []
        self.groups: list['NodeEditorGroup'] = []

        self.in_points:   list['Point2D']    = []
        self.in_sockets:  list['NodeSocket'] = []
        self.out_points:  list['Point2D']    = []
        self.out_sockets: list['NodeSocket'] = []

        self.future_link: Scalar2D = None
        self.rubber_band: Scalar2D = None

        self.selected_nodes: 'list'['NodeFrame'] = []
        self.removed_socket: 'NodeSocket'        = None

        self._prev_zoom: float = 1.0
        self._curr_zoom: float = 1.0



@Gtk.Template(resource_path = '/com/macipra/witt/node/editor.ui')
class NodeEditor(Gtk.Overlay):

    __gtype_name__ = 'NodeEditor'

    ScrolledWindow = Gtk.Template.Child()
    Canvas         = Gtk.Template.Child()
    Minimap        = Gtk.Template.Child()
    MinimapToggle  = Gtk.Template.Child()

    ICON_NAME     = 'user-home-symbolic'
    ACTION_PREFIX = 'node'

    title = GObject.Property(type = str, default = _('Home'))

    def __init__(self,
                 nodes: list['NodeFrame'] = [],
                 links: list['NodeLink']  = [],
                 ) ->   None:
        """"""
        super().__init__()

        viewport = self.ScrolledWindow.get_first_child()
        viewport.set_scroll_to_focus(False)

        self.nodes:  list['NodeFrame']       = []
        self.links:  list['NodeLink']        = []
        self.groups: list['NodeEditorGroup'] = []

        self.in_points:   list['Point2D']    = []
        self.in_sockets:  list['NodeSocket'] = []
        self.out_points:  list['Point2D']    = []
        self.out_sockets: list['NodeSocket'] = []

        self.future_link: Scalar2D = None
        self.rubber_band: Scalar2D = None

        self.selected_nodes: list['NodeFrame'] = []

        self.removed_link:   'NodeLink'   = None
        self.removed_socket: 'NodeSocket' = None

        self._prev_zoom = 1.0
        self._curr_zoom = 1.0

        style_manager   = Adw.StyleManager.get_default()
        self._prev_dark = style_manager.get_dark()
        self._curr_dark = self._prev_dark

        self._dots_grid_texture = None

        self._cursor_x_position = 0
        self._cursor_y_position = 0

        self._origin_x_position = 0
        self._origin_y_position = 0

        self._editor_init_setup = False
        self._should_init_nodes = len(nodes) > 0

        self._setup_data(nodes, links)
        self._setup_actions()
        self._setup_commands()
        self._setup_controllers()

    def setup(self) -> None:
        """"""
        pass

    def grab_focus(self) -> None:
        """"""
        self.Canvas.set_focusable(True)
        self.Canvas.grab_focus()

    def refresh_ui(self) -> None:
        """"""
        window = self.get_root()

        GLib.idle_add(window.Toolbar.populate)
        GLib.idle_add(window.StatusBar.populate)

        self.queue_draw()

    def cleanup(self) -> None:
        """"""
        pass

    def queue_draw(self) -> None:
        """"""
        self.Canvas.queue_draw()
        if self.Minimap.get_visible():
            self.Minimap.queue_draw()

    def queue_resize(self) -> None:
        """"""
        Gtk.Widget.queue_resize(self)
        self.queue_draw()

    def get_command_list(self) -> list[dict]:
        """"""
        from ..core.parser_command_context import Transformer
        from ..core.parser_command_context import parser

        variables = {}

        variables['node_focus'] = len(self.selected_nodes) > 0

        def isrelevant(context: str
                       ) ->     bool:
            """"""
            if context is None:
                return True
            try:
                tree = parser.parse(context)
                transformer = Transformer(variables)
                return transformer.transform(tree)
            except:
                return False

        command_list = []
        for command in self._command_list:
            if not isrelevant(command['context']):
                continue
            command_list.append(command)

        return command_list

    def _setup_data(self,
                    nodes: list['NodeFrame'] = [],
                    links: list['NodeLink']  = [],
                    ) ->   None:
        """"""
        window = env.app.get_active_main_window()
        window.history.freezing = True

        for node in nodes:
            self.add_node(node)

        for link in links:
            if link.in_socket.Frame not in nodes:
                continue
            if link.out_socket.Frame not in nodes:
                continue
            self.links.append(link)

        window.history.freezing = False

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

        def create_node(name: str) -> None:
            """"""
            self.activate_action('node.create', GLib.Variant('s', name))

        create_action('open-file',              callback   = lambda *_: self.activate_action('app.open-file'))

        create_action('create',                 callback   = self._on_create_action,
                                                param_type = GLib.VariantType('s'))

        create_action('duplicate',              callback   = self._on_duplicate_action,
                                                shortcuts  = ['<Primary>d'])
        create_action('delete',                 callback   = self._on_delete_action,
                                                shortcuts  = ['Delete'])
        create_action('select-all',             callback   = self._on_select_all_action,
                                                shortcuts  = ['<Primary>a'])
        create_action('select-none',            callback   = self._on_select_none_action,
                                                shortcuts  = ['<Shift><Primary>a'])

#       create_action('link',                   callback   = lambda *_: None)
#       create_action('unlink',                 callback   = lambda *_: None)

#       create_action('group',                  callback   = lambda *_: None,
#                                               shortcuts  = ['<Primary>g'])
#       create_action('ungroup',                callback   = lambda *_: None,
#                                               shortcuts  = ['<Shift><Primary>g'])

#       create_action('mute',                   callback   = lambda *_: None,
#                                               shortcuts  = ['m'])
#       create_action('collapse',               callback   = lambda *_: None,
#                                               shortcuts  = ['h'])

        create_action('read-file',              lambda *_: create_node('read-file'))

        create_action('choose-columns',         lambda *_: create_node('choose-columns'))
        create_action('remove-columns',         lambda *_: create_node('remove-columns'))

        create_action('keep-top-k-rows',        lambda *_: create_node('keep-top-k-rows'))
        create_action('keep-bottom-k-rows',     lambda *_: create_node('keep-bottom-k-rows'))
        create_action('keep-first-k-rows',      lambda *_: create_node('keep-first-k-rows'))
        create_action('keep-last-k-rows',       lambda *_: create_node('keep-last-k-rows'))
        create_action('keep-range-of-rows',     lambda *_: create_node('keep-range-of-rows'))
        create_action('keep-every-nth-rows',    lambda *_: create_node('keep-every-nth-rows'))
        create_action('keep-duplicate-rows',    lambda *_: create_node('keep-duplicate-rows'))

        create_action('remove-first-k-rows',    lambda *_: create_node('remove-first-k-rows'))
        create_action('remove-last-k-rows',     lambda *_: create_node('remove-last-k-rows'))
        create_action('remove-range-of-rows',   lambda *_: create_node('remove-range-of-rows'))
        create_action('remove-duplicate-rows',  lambda *_: create_node('remove-duplicate-rows'))

        create_action('sort-rows',              lambda *_: create_node('sort-rows'))

        create_action('new-sheet',              lambda *_: create_node('new-sheet'))
        create_action('new-viewer',             lambda *_: create_node('new-viewer'))

        create_action('new-boolean',            lambda *_: create_node('new-boolean'))
        create_action('new-decimal',            lambda *_: create_node('new-decimal'))
        create_action('new-integer',            lambda *_: create_node('new-integer'))
        create_action('new-string',             lambda *_: create_node('new-string'))

        create_action('transpose-table',        lambda *_: create_node('transpose-table'))
        create_action('reverse-rows',           lambda *_: create_node('reverse-rows'))

        create_action('convert-data-type',      lambda *_: create_node('convert-data-type'))
        create_action('rename-columns',         lambda *_: create_node('rename-columns'))

    def _setup_commands(self) -> None:
        """"""
        self._command_list = []

        def create_command(action_name: str,
                           title:       str,
                           name:        str          = None,
                           action_args: GLib.Variant = None,
                           shortcuts:   list[str]    = [],
                           context:     str          = None,
                           prefix:      str          = 'node',
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

        create_command('duplicate',             f"{_('Selection')}: {_('Duplicate Node(s)')}",
                                                shortcuts = ['<Primary>d'],
                                                context   = 'node_focus')
        create_command('delete',                f"{_('Selection')}: {_('Delete Node(s)')}",
                                                shortcuts = ['Delete'],
                                                context   = 'node_focus')
        create_command('select-all',            f"{_('Selection')}: {_('Select All')}",
                                                shortcuts = ['<Primary>a'])
        create_command('select-none',           f"{_('Selection')}: {_('Select None')}",
                                                shortcuts = ['<Shift><Primary>a'],
                                                context   = 'node_focus')

        create_command('open-file',             _('Open File...'),
                                                shortcuts = ['<Primary>o'],
                                                prefix    = 'app')

        create_command('read-file',             f"{_('Create')}: {_('Read File')}")

        create_command('choose-columns',        f"{_('Table')}: {_('Choose Columns')}")
        create_command('remove-columns',        f"{_('Table')}: {_('Remove Columns')}")

        create_command('keep-rows',             '$placeholder') # TODO: find a better way?
        create_command('keep-top-k-rows',       f"{_('Table')}: {_('Keep Top K Rows')}")
        create_command('keep-bottom-k-rows',    f"{_('Table')}: {_('Keep Bottom K Rows')}")
        create_command('keep-first-k-rows',     f"{_('Table')}: {_('Keep First K Rows')}")
        create_command('keep-last-k-rows',      f"{_('Table')}: {_('Keep Last K Rows')}")
        create_command('keep-range-of-rows',    f"{_('Table')}: {_('Keep Range of Rows')}")
        create_command('keep-every-nth-rows',   f"{_('Table')}: {_('Keep Every nth Rows')}")
        create_command('keep-duplicate-rows',   f"{_('Table')}: {_('Keep Duplicate Rows')}")

        create_command('remove-rows',           '$placeholder')
        create_command('remove-first-k-rows',   f"{_('Table')}: {_('Remove First K Rows')}")
        create_command('remove-last-k-rows',    f"{_('Table')}: {_('Remove Last K Rows')}")
        create_command('remove-range-of-rows',  f"{_('Table')}: {_('Remove Range of Rows')}")
        create_command('remove-duplicate-rows', f"{_('Table')}: {_('Remove Duplicate Rows')}")

        create_command('sort-rows',             f"{_('Table')}: {_('Sort Rows')}")

        create_command('new-sheet',             f"{_('Create')}: {_('Sheet')}")
        create_command('new-viewer',            f"{_('Create')}: {_('Viewer')}")
        create_command('new-boolean',           f"{_('Create')}: {_('Constant')} {_('Boolean')}")
        create_command('new-decimal',           f"{_('Create')}: {_('Constant')} {_('Decimal')}")
        create_command('new-integer',           f"{_('Create')}: {_('Constant')} {_('Integer')}")
        create_command('new-string',            f"{_('Create')}: {_('Constant')} {_('String')}")
        create_command('new-constants',         '$placeholder')

        create_command('transpose-table',       f"{_('Table')}: {_('Transpose')}")
        create_command('reverse-rows',          f"{_('Table')}: {_('Reverse')}")

        create_command('convert-data-type',     f"{_('Table')}: {_('Convert Data Type')}")
        create_command('rename-columns',        f"{_('Table')}: {_('Rename Columns')}")

    def _setup_controllers(self) -> None:
        """"""
        controller = Gtk.EventControllerMotion()
        controller.connect('motion', self._on_motion)
        self.add_controller(controller)

        vadjustment = self.ScrolledWindow.get_vadjustment()
        hadjustment = self.ScrolledWindow.get_hadjustment()
        hadjustment.connect('value-changed', lambda *_: self.queue_draw())
        vadjustment.connect('value-changed', lambda *_: self.queue_draw())

        controller = Gtk.GestureDrag.new()
        controller.set_button(Gdk.BUTTON_MIDDLE)
        controller.connect('drag-begin', self._on_pan_begin)
        controller.connect('drag-update', self._on_pan_update)
        controller.connect('drag-end', self._on_pan_end)
        self.Canvas.add_controller(controller)

        self.MinimapToggle.bind_property('active', self.Minimap, 'visible', GObject.BindingFlags.SYNC_CREATE)

    def _on_motion(self,
                   motion: Gtk.EventControllerMotion,
                   x:      float,
                   y:      float,
                   ) ->    None:
        """"""
        vadjustment = self.ScrolledWindow.get_vadjustment()
        hadjustment = self.ScrolledWindow.get_hadjustment()
        scroll_y_position = vadjustment.get_value()
        scroll_x_position = hadjustment.get_value()

        self._cursor_x_position = x + scroll_x_position
        self._cursor_y_position = y + scroll_y_position

    def _on_pan_begin(self,
                      gesture: Gtk.GestureDrag,
                      start_x: float,
                      start_y: float,
                      ) ->     None:
        """"""
        self.Canvas.set_cursor(Gdk.Cursor.new_from_name('grabbing', None))

    def _on_pan_update(self,
                       gesture:  Gtk.GestureDrag,
                       offset_x: float,
                       offset_y: float,
                       ) ->      None:
        """"""
        vadjustment = self.ScrolledWindow.get_vadjustment()
        hadjustment = self.ScrolledWindow.get_hadjustment()
        scroll_y_position = vadjustment.get_value()
        scroll_x_position = hadjustment.get_value()

        vadjustment.set_value(scroll_y_position - offset_y)
        hadjustment.set_value(scroll_x_position - offset_x)

    def _on_pan_end(self,
                    gesture:  Gtk.GestureDrag,
                    offset_x: float,
                    offset_y: float,
                    ) ->      None:
        """"""
        self.Canvas.set_cursor(None)

    def _setup_default_nodes(self) -> None:
        """"""
        from .repository import NodeSheet
        from .repository import NodeViewer

        canvas_width = self.Canvas.get_width()
        canvas_height = self.Canvas.get_height()

        window = self.get_root()
        viewport_width = window.TabView.get_width()
        viewport_height = window.TabView.get_height()

        scroll_x_position = (canvas_width  - viewport_width)  / 2
        scroll_y_position = (canvas_height - viewport_height) / 2

        # TODO: the geometry in the calculation should be made to be
        # more representative of the actual geometry of the nodes

        offset = 175 / 2 + 50 / 2
        x_position = scroll_x_position + (viewport_width  - 175) / 2
        y_position = scroll_y_position + (viewport_height - 111) / 2

        viewer = NodeViewer.new(x_position + offset, y_position)
        sheet = NodeSheet.new(x_position - offset, y_position)

        in_socket = sheet.contents[0].Socket
        out_socket = viewer.contents[-1].Socket

        window.history.freezing = True

        self.add_node(viewer)
        self.add_node(sheet)
        self.add_link(in_socket, out_socket)

        window.history.freezing = False

        vadjustment = self.ScrolledWindow.get_vadjustment()
        hadjustment = self.ScrolledWindow.get_hadjustment()
        vadjustment.set_value(scroll_y_position)
        hadjustment.set_value(scroll_x_position)

    def _fit_nodes_to_viewport(self) -> None:
        """"""
        # TODO: implement viewport' zoom
        # TODO: adjust zoom to fit nodes

        scroll_x_position = self.Canvas.get_width()
        scroll_y_position = self.Canvas.get_height()

        for node in self.nodes:
            scroll_x_position = min(scroll_x_position, node.x)
            scroll_y_position = min(scroll_y_position, node.y)

        vadjustment = self.ScrolledWindow.get_vadjustment()
        hadjustment = self.ScrolledWindow.get_hadjustment()
        vadjustment.set_value(scroll_y_position - 50)
        hadjustment.set_value(scroll_x_position - 50)

    def do_collect_points(self,
                          nodes: list['NodeFrame'] = [],
                          ) ->   None:
        """"""
        self.queue_resize()
        if not nodes:
            nodes = self.nodes
        for node in nodes:
            node.compute_points()
        self.collect_points()

    def do_map(self) -> None:
        """"""
        Gtk.Box.do_map(self)

        def do_init_setup() -> bool:
            """"""
            window = self.get_root()

            if not window:
                return Gdk.EVENT_STOP
            if not window.TabView.get_width():
                return Gdk.EVENT_STOP

            if not self._editor_init_setup:
                if not self.nodes:
                    self._setup_default_nodes()
                if self._should_init_nodes:
                    self._fit_nodes_to_viewport()
                self._editor_init_setup = True

            GLib.timeout_add(50, self.do_collect_points)

            return Gdk.EVENT_PROPAGATE

        GLib.idle_add(do_init_setup)

    def do_snapshot(self,
                    snapshot: Gtk.Snapshot,
                    ) ->      None:
        """"""
        self._style_manager = Adw.StyleManager.get_default()
        self._curr_dark = self._style_manager.get_dark()

        self._draw_dots_grid(snapshot)

        child = self.get_first_child()
        while child:
            self.snapshot_child(child, snapshot)
            child = child.get_next_sibling()

    def _draw_dots_grid(self,
                        snapshot: Gtk.Snapshot,
                        ) ->      None:
        """"""
        vadjustment = self.ScrolledWindow.get_vadjustment()
        hadjustment = self.ScrolledWindow.get_hadjustment()
        scroll_y_position = vadjustment.get_value()
        scroll_x_position = hadjustment.get_value()

        width = self.get_width()
        height = self.get_height()

        minor_step = 25
        major_step = minor_step * 5

        def do_draw() -> None:
            """"""
            y = -(scroll_y_position % major_step)
            while y <= height:
                x = -(scroll_x_position % major_step)
                while x <= width:
                    bounds = Graphene.Rect().init(x, y, major_step, major_step)
                    snapshot.append_texture(self._dots_grid_texture, bounds)
                    x += major_step
                y += major_step

        has_texture = self._dots_grid_texture is not None
        zoom_changed = self._prev_zoom == self._curr_zoom
        style_changed = self._prev_dark == self._curr_dark
        if has_texture and zoom_changed and style_changed:
            do_draw()
            return

        self._prev_zoom = self._curr_zoom
        self._prev_dark = self._curr_dark

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, major_step, major_step)
        context = cairo.Context(surface)
        context.set_antialias(cairo.Antialias.NONE)

        if self._curr_dark:
            color = (0.25, 0.25, 0.25, 1.0)
        else:
            color = (0.85, 0.85, 0.85, 1.0)
        context.set_source_rgba(*color)

        y = 0.0
        while y <= major_step:
            x = 0.0
            while x <= major_step:
                context.arc(x, y, 1.0, 0, 2 * math.pi)
                context.fill()
                if (
                    y % major_step == 0 and
                    x % major_step == 0
                ):
                    context.arc(x, y, 2.0, 0, 2 * math.pi)
                    context.fill()
                x += minor_step
            y += minor_step

        pixbuf = GdkPixbuf.Pixbuf.new_from_data(data            = surface.get_data(),
                                                colorspace      = GdkPixbuf.Colorspace.RGB,
                                                has_alpha       = True,
                                                bits_per_sample = 8,
                                                width           = major_step,
                                                height          = major_step,
                                                rowstride       = surface.get_stride())
        self._dots_grid_texture = Gdk.Texture.new_for_pixbuf(pixbuf)

        do_draw()

    def do_close_page(self,
                      tab_page: Adw.TabPage,
                      ) ->      None:
        """"""
        from .repository import NodeViewer

        # Find and unlink the related nodes
        for node in self.nodes:
            if isinstance(node.parent, NodeViewer):
                for content in node.contents:
                    if content.Page == tab_page:
                        if links := content.Socket.links:
                            link = links[0]
                            if link not in self.links:
                                break
                            self.links.remove(link)
                            link.unlink()
                        if content in node.contents:
                            node.remove_content(content)
                        break
                else:
                    continue
                break

        gc.collect()

    def _on_create_action(self,
                          action:    Gio.SimpleAction,
                          parameter: GLib.Variant,
                          ) ->       None:
        """"""
        # TODO: it's yet to be determined when requested from
        # 1) the primary toolbar, 2) the contextual menu, and
        # 3) the command palette for the placement algorithm.
        vadjustment = self.ScrolledWindow.get_vadjustment()
        hadjustment = self.ScrolledWindow.get_hadjustment()
        scroll_y_position = vadjustment.get_value()
        scroll_x_position = hadjustment.get_value()

        name = parameter.get_string()
        node = self.create_node(name,
                                scroll_x_position + 50,#self._cursor_x_position
                                scroll_y_position + 50)#self._cursor_y_position

        if node:
            window = self.get_root()
            window.history.grouping = True
            self.add_node(node)
            self.select_by_click(node)
            window.history.grouping = False

    def _on_duplicate_action(self,
                             action:    Gio.SimpleAction,
                             parameter: GLib.Variant,
                             ) ->       None:
        """"""
        if not self.selected_nodes:
            return

        window = self.get_root()
        window.history.grouping = True

        selected = copy(self.selected_nodes)

        self.select_by_click()

        for node in selected:
            cloned = node.parent.clone()
            self.add_node(cloned)
            self.select_by_click(cloned, True)

        # TODO: replicate the links from/to cloned nodes

        window.history.grouping = False

        GLib.timeout_add(50, self.do_collect_points, self.selected_nodes)

    def _on_delete_action(self,
                          action:    Gio.SimpleAction,
                          parameter: GLib.Variant,
                          ) ->       None:
        """"""
        if not self.selected_nodes:
            return

        from .action import ActionDeleteNode
        action = ActionDeleteNode(self, self.selected_nodes)

        window = self.get_root()
        window.do(action)

    def _on_select_all_action(self,
                              action:    Gio.SimpleAction,
                              parameter: GLib.Variant,
                              ) ->       None:
        """"""
        from .repository import NodeViewer

        window = self.get_root()
        window.history.grouping = True

        self.select_by_click()

        for node in self.nodes:
            self.select_by_click(node, True)

            if isinstance(node.parent, NodeViewer):
                self.select_viewer(node)

        window.history.grouping = False

    def _on_select_none_action(self,
                               action:    Gio.SimpleAction,
                               parameter: GLib.Variant,
                               ) ->       None:
        """"""
        self.select_by_click()

    def create_node(self,
                    name: 'str',
                    x:    'int' = 0,
                    y:    'int' = 0,
                    ) ->  'NodeFrame':
        """"""
        from .repository import create_new_node
        return create_new_node(name, x, y)

    def add_node(self,
                 node: 'NodeFrame',
                 ) ->  'bool':
        """"""
        from .action import ActionAddNode
        action = ActionAddNode(self, [node])
        window = self.get_window()
        return window.do(action)

    def add_link(self,
                 socket1: 'NodeSocket',
                 socket2: 'NodeSocket',
                 ) ->     'bool':
        """"""
        from .action import ActionAddLink
        action = ActionAddLink(self, socket1, socket2)
        window = self.get_window()
        return window.do(action)

    def collect_points(self) -> None:
        """"""
        self.in_points   = []
        self.in_sockets  = []
        self.out_points  = []
        self.out_sockets = []

        for node in self.nodes:
            self.in_points   += node.in_points
            self.in_sockets  += node.in_sockets
            self.out_points  += node.out_points
            self.out_sockets += node.out_sockets

    def begin_future_link(self,
                          scalar: 'Scalar2D',
                          socket: 'NodeSocket',
                          ) ->    'None':
        """"""
        self._source_socket = socket
        self._target_socket = None

        self._build_snap_points(socket.socket_type)
        self.update_future_link(scalar)

    def update_future_link(self,
                           scalar: Scalar2D,
                           ) ->    None:
        """"""
        self.future_link = scalar
        self._snap_future_link()
        self.Canvas.queue_draw()

    def end_future_link(self) -> None:
        """"""
        window = self.get_window()

        window.history.grouping = True

        if self._target_socket:
            if is_linked := len(self._target_socket.links) > 0:
                from .action import ActionEditNode
                frame = self._target_socket.Frame
                old_value = frame.do_save()
                values = (old_value, old_value)
                action = ActionEditNode(self, frame, values)
                window.do(action, add_only = True)

            self.add_link(self._source_socket, self._target_socket)

            if is_linked:
                new_value = frame.do_save()
                if old_value == new_value:
                    window.history.undo_stack.remove(action)
                else:
                    action.values = (old_value, new_value)

            if self._target_socket == self.removed_socket:
                self.removed_link   = None
                self.removed_socket = None

        if self.removed_link:
            from .action import ActionDeleteLink
            action = ActionDeleteLink(self, self.removed_link)
            window.do(action, add_only = True)

        if self.removed_socket:
            from .action import ActionDeleteNodeContent
            content = self.removed_socket.Content
            action = ActionDeleteNodeContent(self, content)
            window.do(action)

        window.history.grouping = False

        self._source_socket = None
        self._target_socket = None
        self.removed_link   = None
        self.removed_socket = None

        self._clean_snap_points()
        self.update_future_link(None)

        gc.collect()

        GLib.timeout_add(50, self.do_collect_points)

    def _build_snap_points(self,
                           socket_type: 'NodeSocketType',
                           ) ->         'None':
        """"""
        if socket_type == NodeSocketType.INPUT:
            points = narray(self.out_points)
        if socket_type == NodeSocketType.OUTPUT:
            points = narray(self.in_points)

        self._snap_points = spatial.KDTree(points)
        self._socket_type = socket_type

    def _snap_future_link(self) -> None:
        """"""
        if not self._snap_points:
            return

        # Reset the target socket so that it won't be picked up
        # when the user release the pointer from the future-link
        self._target_socket = None

        # Find the nearest socket from the end-point of the future-link
        point = narray(self.future_link[1]).reshape(1, -1)
        distance, index = self._snap_points.query(point, k = 1)
        distance, index = distance[0], index[0]

        # Skip if the nearest target is too far from the source socket
        if distance > 18:
            return

        if self._socket_type == NodeSocketType.INPUT:
            target_point = self.out_points[index]
            target_socket = self.out_sockets[index]
        if self._socket_type == NodeSocketType.OUTPUT:
            target_point = self.in_points[index]
            target_socket = self.in_sockets[index]

        # Skip if the target socket inside the same node as the source
        target_node = target_socket.Content.Frame
        source_node = self._source_socket.Content.Frame
        if source_node == target_node:
            return

        # Snap the future-link to the target socket coordinate
        point_1 = self.future_link[0]
        point_2 = (target_point[0], target_point[1])
        self.future_link = (point_1, point_2)

        self._target_socket = target_socket

    def _clean_snap_points(self) -> None:
        """"""
        self._snap_points = None
        self._socket_type = None

    def begin_move_selections(self) -> None:
        """"""
        canvas_width  = self.Canvas.get_width()
        canvas_height = self.Canvas.get_height()

        # Calculate maximum position to prevent the nodes
        # from go beyond the canvas boundaries which will
        # make them no longer accessible
        for node in self.selected_nodes:
            node_width  = node.get_width()
            node_height = node.get_height()
            node._max_x = canvas_width  - node_width
            node._max_y = canvas_height - node_height
            node._old_x = node.x
            node._old_y = node.y

        self._origin_x_position = self._cursor_x_position
        self._origin_y_position = self._cursor_y_position

    def update_move_selections(self,
                               offset_x: float,
                               offset_y: float,
                               ) ->      None:
        """"""
        offset_x = self._cursor_x_position - self._origin_x_position
        offset_y = self._cursor_y_position - self._origin_y_position

        if abs(offset_x) < 1 and abs(offset_y) < 1:
            return

        for node in self.selected_nodes:
            node.x = int(min(max(0, node._old_x + offset_x), node._max_x))
            node.y = int(min(max(0, node._old_y + offset_y), node._max_y))
            self.Canvas.move(node, node.x, node.y)

        self.queue_draw()

    def end_move_selections(self) -> None:
        """"""
        offset_x = self._cursor_x_position - self._origin_x_position
        offset_y = self._cursor_y_position - self._origin_y_position

        if abs(offset_x) < 1 and abs(offset_y) < 1:
            return

        for node in self.selected_nodes:
            old_position = (node._old_x, node._old_y)
            new_position = (node.x, node.y)
            positions = (old_position, new_position)
            self.move_node(node, positions)

    def move_node(self,
                  node:      'NodeFrame',
                  positions: 'tuple',
                  ) ->       'None':
        """"""
        from .action import ActionMoveNode
        action = ActionMoveNode(self, [node], [positions])
        window = self.get_root()
        window.do(action)

    def select_viewer(self,
                      viewer: 'NodeFrame',
                      ) ->    'bool':
        """"""
        from .action import ActionSelectViewer
        action = ActionSelectViewer(self, viewer)
        window = self.get_window()
        return window.do(action)

    def select_by_click(self,
                        node:  'NodeFrame' = None,
                        combo: 'bool'      = False,
                        ) ->   'bool':
        """"""
        from .action import ActionSelectByClick
        action = ActionSelectByClick(self, node, combo)
        window = self.get_window()
        return window.do(action)

    def select_by_rubberband(self,
                             combo: bool,
                             ) ->   bool:
        """"""
        p1, p2 = self.rubber_band
        x1, y1 = p1
        x2, y2 = p2

        if abs(x2 - x1) < 1 and abs(y2 - y1) < 1:
            return False

        from .action import ActionSelectByRubberband
        action = ActionSelectByRubberband(self, combo)
        window = self.get_window()
        return window.do(action)

    def get_window(self) -> Gtk.Window:
        """"""
        if window := self.get_root():
            return window
        return env.app.get_active_main_window()

from .frame import NodeFrame
from .socket import NodeSocket
from .socket import NodeSocketType
from .link import NodeLink
