# custom_formula.py
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

from gi.repository import Gtk
from typing import Any
import logging

from ._template import NodeTemplate
from ._utils import iscompatible
from ._utils import take_snapshot

from ..content import NodeContent
from ..frame import NodeFrame
from ..socket import NodeSocket
from ..socket import NodeSocketType
from ..widgets import NodeFormulaEditor
from ..widgets import NodeLabel

logger = logging.getLogger(__name__)

class NodeCustomFormula(NodeTemplate):

    ndname = _('Custom Formula')

    action = 'custom-formula'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeCustomFormula(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['formula']   = 'value'
        self.frame.data['signature'] = None

        self._add_output()
        self._add_input()
        self._add_editor()

        def on_refresh(button: Gtk.Button) -> None:
            """"""
            self.frame.data['signature'] = None
            self.frame.do_execute(backward = False)
        self.frame.CacheButton.connect('clicked', on_refresh)

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['formula'] = args[0]

        widget = self.frame.contents[2].Widget
        widget.set_data(args[0])

        self.frame.data['signature'] = None

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        in_content = self.frame.contents[1]

        out_content = self.frame.contents[0]
        out_socket = out_content.Socket

        is_isolated = len(out_content.Socket.links) == 0 and \
                      len(in_content.Socket.links)  == 0

        if is_isolated:
            self.frame.data['value'] = None
            out_socket.set_data_type(Any)
            return

        value = None

        if links := in_content.Socket.links:
            pair_content = links[0].in_socket.Content
            value = pair_content.get_data()
            out_socket.set_data_type(type(value))

        formula = self.frame.data['formula']

        if not formula:
            self.frame.data['value'] = value
            return

        signature = (id(value), formula)

        if self.frame.data['signature'] == signature:
            return

        # Evaluate custom formula
        from ....core.evaluators.formula import Evaluator
        try:
            variables = {'value': value}
            value = Evaluator(variables).evaluate(formula)
            out_socket.set_data_type(type(value))
        except Exception as e:
            logger.error(e, exc_info = True)
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

        from polars import DataFrame
        from polars import LazyFrame

        if out_socket.data_type == LazyFrame:
            out_socket.set_data_type(DataFrame)

        if isinstance(value, DataFrame):
            value = value.lazy()
            self.frame.data['signature'] = signature
            self.frame.CacheButton.set_visible(True)
        else:
            self.frame.CacheButton.set_visible(False)

        self.frame.data['value'] = value

    def do_save(self) -> str:
        """"""
        return self.frame.data['formula']

    def do_restore(self,
                   value: str,
                   ) ->   None:
        """"""
        try:
            self.set_data(value)
        except Exception as e:
            logger.error(e, exc_info = True)
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

    def _add_output(self) -> None:
        """"""
        self.frame.data['value'] = None

        def get_data() -> Any:
            """"""
            return self.frame.data['value']

        def set_data(value: Any) -> None:
            """"""
            self.frame.data['value'] = value
            self.frame.do_execute(backward = False)

        widget = NodeLabel(_('Value'))
        socket_type = NodeSocketType.OUTPUT
        self.frame.add_content(widget      = widget,
                               socket_type = socket_type,
                               data_type   = None,
                               get_data    = get_data,
                               set_data    = set_data)

    def _add_input(self) -> None:
        """"""
        label = NodeLabel(_('Value'), can_link = True)
        socket_type = NodeSocketType.INPUT
        content = self.frame.add_content(widget      = label,
                                         socket_type = socket_type)

        def do_link(pair_socket:  NodeSocket,
                    self_content: NodeContent,
                    ) ->          None:
            """"""
            if not iscompatible(pair_socket, self_content):
                return

            self.frame.data['signature'] = None

            self.frame.do_execute(pair_socket, self_content)

        content.do_link = do_link

        def do_unlink(socket: NodeSocket) -> None:
            """"""
            self.frame.data['signature'] = None

            self.frame.do_execute(self_content = socket.Content,
                                  backward     = False)

        content.do_unlink = do_unlink

    def _add_editor(self) -> None:
        """"""
        def get_data() -> str:
            """"""
            return self.frame.data['formula']

        def set_data(value: str) -> None:
            """"""
            def callback(value: str) -> None:
                """"""
                self.frame.data['formula'] = value
                self.frame.data['signature'] = None
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        widget = NodeFormulaEditor(get_data = get_data,
                                   set_data = set_data)
        self.frame.add_content(widget   = widget,
                               get_data = get_data,
                               set_data = set_data)