# read_database.py
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

from copy          import deepcopy
from gi.repository import Gtk
from typing        import Any

import logging

from ._template import NodeTemplate
from ._utils    import take_snapshot

from ..content import NodeContent
from ..frame   import NodeFrame
from ..frame   import NodeFrameType
from ..socket  import NodeSocket
from ..socket  import NodeSocketType
from ..widgets import NodeDatabaseReader
from ..widgets import NodeLabel

logger = logging.getLogger(__name__)

class NodeReadDatabase(NodeTemplate):

    ndname = _('Read Database')

    action = 'read-database'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeReadDatabase(x, y)

        self.frame.node_type  = NodeFrameType.SOURCE
        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['query']     = 'SELECT 1'
        self.frame.data['config']    = {}
        self.frame.data['file-path'] = ''
        self.frame.data['signature'] = None

        self._add_output()
        self._add_editor()

        def on_refresh(button: Gtk.Button) -> None:
            """"""
            self.frame.data['signature'] = None
            self.frame.do_execute(backward = False)
        self.frame.CacheButton.connect('clicked', on_refresh)

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        query  = args[0]
        config = args[1]

        self.frame.data['query']  = query
        self.frame.data['config'] = config

        widget = self.frame.contents[1].Widget
        widget.set_data(args[0])

        self.frame.data['signature'] = None

        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        out_content = self.frame.contents[0]
        out_socket = out_content.Socket

        if not out_content.Socket.links:
            self.frame.data['value'] = None
            out_socket.set_data_type(Any)
            return

        query  = self.frame.data['query']
        config = self.frame.data['config']

        if not query:
            self.frame.data['value'] = None
            out_socket.set_data_type(None)
            return

        signature = (query, id(config))

        if self.frame.data['signature'] == signature:
            return

        from polars import DataFrame
        from polars import LazyFrame
        from ....backend.database import Database

        if file_path := self.frame.data['file-path']:
            try:
                import os
                os.remove(file_path)
            except Exception as e:
                logger.error(e, exc_info = True)
            self.frame.data['file-path'] = ''

        config = deepcopy(config)

        # Get password from system keyring
        if config.get('host'):
            from keyring import get_password
            username = Database.hash_config(config)
            password = get_password('com.wittara.studio', username)
            config['password'] = password or ''

        output, log_info = Database.execute(dialect = config['dialect'],
                                                     config  = config,
                                                     query   = query)

        # Hide password from log message
        if (password := config.get('password')) and (message := log_info['message']):
            log_info['message'] = message.replace(password, '*' * len(password))

        if log_info['success']:
            self.frame.data['file-path'] = log_info['fpath']
            self.frame.data['signature'] = signature
            self.frame.CacheButton.set_visible(True)
            self.frame.ErrorButton.set_visible(False)
        else:
            self.frame.CacheButton.set_visible(False)
            self.frame.ErrorButton.set_tooltip_text(log_info['message'])
            self.frame.ErrorButton.set_visible(True)

        if not isinstance(output, LazyFrame):
            output = None

        out_socket.set_data_type(type(output))
        if out_socket.data_type == LazyFrame:
            out_socket.set_data_type(DataFrame)

        self.frame.data['value'] = output

    def do_save(self) -> dict:
        """"""
        return {
            'query':  self.frame.data['query'],
            'config': deepcopy(self.frame.data['config']),
        }

    def do_restore(self,
                   value: dict,
                   ) ->   None:
        """"""
        try:
            self.set_data(value['query'],
                          value['config'])
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

    def _add_editor(self) -> None:
        """"""
        def get_data() -> Any:
            """"""
            return self.do_save()

        def set_data(*args, **kwargs) -> None:
            """"""
            take_snapshot(self, self.set_data, *args, **kwargs)

        widget = NodeDatabaseReader(get_data = get_data,
                                    set_data = set_data)
        self.frame.add_content(widget   = widget,
                               get_data = get_data,
                               set_data = set_data)