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

from ..core.action import Action

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

        self.selected_nodes: 'list'['NodeFrame'] = []
        self.removed_socket: 'NodeSocket'        = None

        self._prev_zoom: float = 1.0
        self._curr_zoom: float = 1.0

        style_manager   = Adw.StyleManager.get_default()
        self._prev_dark = style_manager.get_dark()
        self._curr_dark = self._prev_dark

        self._cursor_x_position: float = 0
        self._cursor_y_position: float = 0

        self._grid_texture = None

        self.is_managing_nodes = False # to group actions
                                       # for undo/redo op

        self._editor_init_setup = False
        self._should_init_nodes = len(nodes) > 0

        for node in nodes:
            self.add_node(node)

        for link in links:
            if link.in_socket.Frame not in nodes:
                continue
            if link.out_socket.Frame not in nodes:
                continue
            self.links.append(link)

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

        from ..window import Window
        if isinstance(window, Window):
            if self == window.get_selected_editor():
                window.Toolbar.populate()

        self.queue_draw()

    def do(self,
           action: Action,
           ) ->    bool:
        """"""
        return False

    def undo(self) -> bool:
        """"""
        return False

    def redo(self) -> bool:
        """"""
        return False

    def cleanup(self) -> None:
        """"""
        pass

    def queue_draw(self) -> None:
        """"""
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

        create_action('new-sheet',              lambda *_: create_node('new-sheet'))
        create_action('new-viewer',             lambda *_: create_node('new-viewer'))

        create_action('new-boolean',            lambda *_: create_node('new-boolean'))
        create_action('new-decimal',            lambda *_: create_node('new-decimal'))
        create_action('new-integer',            lambda *_: create_node('new-integer'))
        create_action('new-string',             lambda *_: create_node('new-string'))

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

        create_command('duplicate',             f"{_('Clipboard')}: {_('Duplicate Node(s)')}",
                                                shortcuts = ['<Primary>d'],
                                                context   = 'node_focus')
        create_command('delete',                f"{_('Clipboard')}: {_('Delete Node(s)')}",
                                                shortcuts = ['Delete'],
                                                context   = 'node_focus')
        create_command('select-all',            f"{_('Clipboard')}: {_('Select All')}",
                                                shortcuts = ['<Primary>a'])
        create_command('select-none',           f"{_('Clipboard')}: {_('Select None')}",
                                                shortcuts = ['<Shift><Primary>a'],
                                                context   = 'node_focus')

        create_command('open-file',             _('Open File...'),
                                                shortcuts = ['<Primary>o'],
                                                prefix    = 'app')

        create_command('read-file',             f"{_('Create')}: {_('Read File')}")

        create_command('new-sheet',             f"{_('Create')}: {_('Sheet')}")
        create_command('new-viewer',            f"{_('Create')}: {_('Viewer')}")

        create_command('new-boolean',           f"{_('Create')}: {_('Constant')} {_('Boolean')}")
        create_command('new-decimal',           f"{_('Create')}: {_('Constant')} {_('Decimal')}")
        create_command('new-integer',           f"{_('Create')}: {_('Constant')} {_('Integer')}")
        create_command('new-string',            f"{_('Create')}: {_('Constant')} {_('String')}")

        create_command('new-constants',         '$placeholder') # TODO: find a better way?

        create_command('choose-columns',        f"{_('Table')}: {_('Choose Columns')}")
        create_command('remove-columns',        f"{_('Table')}: {_('Remove Columns')}")

        create_command('keep-rows',             '$placeholder')
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

    def _setup_controllers(self) -> None:
        """"""
        controller = Gtk.EventControllerMotion()
        controller.connect('motion', self._on_motion)
        self.add_controller(controller)

        vadjustment = self.ScrolledWindow.get_vadjustment()
        hadjustment = self.ScrolledWindow.get_hadjustment()
        hadjustment.connect('value-changed', lambda *_: self.queue_draw())
        vadjustment.connect('value-changed', lambda *_: self.queue_draw())

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

        offset = 175 / 2 + 50 / 2
        x_position = scroll_x_position + (viewport_width  - 175) / 2
        y_position = scroll_y_position + (viewport_height - 111) / 2
        # This is only an estimate and it is no required to be near accurate

        frame1 = NodeViewer.new(x_position + offset, y_position)
        frame2 = NodeSheet.new(x_position - offset, y_position)

        in_socket = frame2.contents[0].Socket
        out_socket = frame1.contents[-1].Socket

        self.add_node(frame1)
        self.add_node(frame2)
        self.add_link(in_socket, out_socket)

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

            if not self.nodes:
                self._setup_default_nodes()
            if self._should_init_nodes:
                self._fit_nodes_to_viewport()

            GLib.idle_add(self.do_collect_points)

            return Gdk.EVENT_PROPAGATE

        if not self._editor_init_setup:
            GLib.idle_add(do_init_setup)
            self._editor_init_setup = True

    def do_snapshot(self,
                    snapshot: Gtk.Snapshot,
                    ) ->      None:
        """"""
        self._style_manager = Adw.StyleManager.get_default()
        self._curr_dark = self._style_manager.get_dark()

        self._draw_grid(snapshot)

        child = self.get_first_child()
        while child:
            self.snapshot_child(child, snapshot)
            child = child.get_next_sibling()

    def _draw_grid(self,
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
                    snapshot.append_texture(self._grid_texture, bounds)
                    x += major_step
                y += major_step

        has_texture = self._grid_texture is not None
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
        self._grid_texture = Gdk.Texture.new_for_pixbuf(pixbuf)

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
            self.add_node(node)
            self.select_by_click(node)

    def _on_duplicate_action(self,
                             action:    Gio.SimpleAction,
                             parameter: GLib.Variant,
                             ) ->       None:
        """"""
        selected = copy(self.selected_nodes)

        # TODO: retain the connection within cloned nodes

        for node in selected:
            cloned = node.parent.clone()
            self.Canvas.put(cloned, cloned.x, cloned.y)
            self.nodes.append(cloned)
            node.unselect()
            cloned.select()

        GLib.idle_add(self.do_collect_points, self.selected_nodes)

        self.queue_draw()

    def _on_delete_action(self,
                          action:    Gio.SimpleAction,
                          parameter: GLib.Variant,
                          ) ->       None:
        """"""
        while self.selected_nodes:
            node = self.selected_nodes[0]
            self.selected_nodes.remove(node)
            self.nodes.remove(node)
            for content in node.contents:
                if not content.Socket:
                    continue
                for link in content.Socket.links:
                    self.links.remove(link)
                    if link.in_socket.auto_remove:
                        content = link.in_socket.Content
                        content.do_remove(content)
                    if link.out_socket.auto_remove:
                        content = link.out_socket.Content
                        content.do_remove(content)
                    link.unlink()
            node.unparent()
            del node

        gc.collect()

        GLib.idle_add(self.do_collect_points)

        self.queue_draw()

    def _on_select_all_action(self,
                              action:    Gio.SimpleAction,
                              parameter: GLib.Variant,
                              ) ->       None:
        """"""
        from .repository import NodeViewer

        self.selected_nodes.clear()

        for node in self.nodes:
            node.select()
            if isinstance(node.parent, NodeViewer):
                self.select_viewer(node)

        self.queue_draw()

    def _on_select_none_action(self,
                               action:    Gio.SimpleAction,
                               parameter: GLib.Variant,
                               ) ->       None:
        """"""
        for node in self.nodes:
            node.unselect()

        self.queue_draw()

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
                 ) ->  'None':
        """"""
        self.Canvas.put(node, node.x, node.y)
        self.nodes.append(node)

        from .repository import NodeViewer
        if isinstance(node.parent, NodeViewer):
            self.select_viewer(node)

        GLib.idle_add(self.do_collect_points, [node])

        # TODO: scroll to the newly added node
        # if the editor is in view, especially
        # if that node is automatically linked
        # and arranged (not at random places).
        # Calling Gtk.Viewport.scroll_to() did
        # not solve the problem unless delayed
        # by a proper timing in which can't be
        # sure to always works.

        self.queue_draw()

    def select_viewer(self,
                      target: 'NodeFrame',
                      ) ->    'None':
        """"""
        from .repository import NodeViewer

        for node in self.nodes:
            if node == target:
                node.set_active(True)
                continue
            if isinstance(node.parent, NodeViewer):
                node.set_active(False)

        # TODO: update window.TabView

        self.queue_draw()

    def add_link(self,
                 socket1: 'NodeSocket',
                 socket2: 'NodeSocket',
                 ) ->     'None':
        """"""
        # Make sure the first socket is from a node output
        if socket1.is_input():
            socket1, socket2 = socket2, socket1

        # Skip if there's already a link between the two sockets
        for link in self.links:
            if link.in_socket == socket1 and link.out_socket == socket2:
                return

        # Unlink the target socket from a linkage if there's any
        # since it doesn't make sense to have multiple inputs.
        # Meanwhile, it makes sense to have multiple outputs from
        # a single socket from any node.
        if socket2.links:
            link = socket2.links[0]
            self.links.remove(link)
            link.unlink()

        link = NodeLink(socket1, socket2)
        self.links.append(link)

        nodes = [socket1.Frame, socket2.Frame]
        GLib.idle_add(self.do_collect_points, nodes)

        self.queue_draw()

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
        # Link the source socket to a target socket if there's any
        if self._target_socket:
            self.add_link(self._source_socket, self._target_socket)

        if self._target_socket == self.removed_socket:
            self.removed_socket = None

        if self.removed_socket:
            content = self.removed_socket.Content
            content.do_remove(content)

        self._source_socket = None
        self._target_socket = None
        self.removed_socket = None

        self._clean_snap_points()
        self.update_future_link(None)

        gc.collect()

        GLib.idle_add(self.do_collect_points)

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
        canvas_width = self.Canvas.get_width()
        canvas_height = self.Canvas.get_height()

        # Calculate maximum position to prevent the nodes
        # from go beyond the canvas boundaries which will
        # make them no longer accessible
        for node in self.selected_nodes:
            node_width = node.get_width()
            node_height = node.get_height()
            node._max_x = canvas_width - node_width
            node._max_y = canvas_height - node_height

    def update_move_selections(self,
                               offset_x: float,
                               offset_y: float,
                               ) ->      None:
        """"""
        for node in self.selected_nodes:
            node.x = int(min(max(0, node.x + offset_x), node._max_x))
            node.y = int(min(max(0, node.y + offset_y), node._max_y))
            self.Canvas.move(node, node.x, node.y)

        self.queue_draw()

    def end_move_selections(self) -> None:
        """"""
        for node in self.selected_nodes:
            node.compute_points()
        self.collect_points()

        gc.collect()

        self.queue_draw()

    def select_by_click(self,
                        node:  'NodeFrame' = None,
                        combo: 'bool'      = False,
                        ) ->   'None':
        """"""
        from .repository import NodeViewer

        self.grab_focus()

        if combo:
            node.toggle()
            if isinstance(node.parent, NodeViewer):
                self.select_viewer(node)
            return

        while self.selected_nodes:
            _node = self.selected_nodes[0]
            _node.unselect()

        if node:
            node.select()
            if isinstance(node.parent, NodeViewer):
                self.select_viewer(node)

        self.refresh_ui()

    def select_by_rubberband(self,
                             combo: bool,
                             ) ->   None:
        """"""
        if not combo:
            while self.selected_nodes:
                node = self.selected_nodes[0]
                node.unselect()

        p1, p2 = self.rubber_band
        x1, y1 = p1
        x2, y2 = p2
        sel_x = min(x1, x2)
        sel_y = min(y1, y2)
        sel_width = abs(x1 - x2)
        sel_height = abs(y1 - y2)
        sel_right = sel_x + sel_width
        sel_bottom = sel_y + sel_height

        for node in self.nodes:
            allocation = node.get_allocation()
            node_x = allocation.x
            node_y = allocation.y
            node_width = allocation.width
            node_height = allocation.height
            node_right = node_x + node_width
            node_bottom = node_y + node_height
            if (
                sel_x      < node_right  and
                sel_right  > node_x      and
                sel_y      < node_bottom and
                sel_bottom > node_y
            ):
                node.toggle()

        self.rubber_band = None

        self.refresh_ui()

from .canvas import NodeCanvas
from .frame import NodeFrame
from .socket import NodeSocket
from .socket import NodeSocketType
from .link import NodeLink
