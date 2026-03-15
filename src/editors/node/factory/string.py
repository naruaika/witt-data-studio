# string.py
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

import logging

from ._template import NodeTemplate
from ._utils    import take_snapshot

from ..frame   import NodeFrame
from ..socket  import NodeSocketType
from ..widgets import NodeEntry

logger = logging.getLogger(__name__)

class NodeString(NodeTemplate):

    ndname = _('String')

    action = 'new-string'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeString(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['value'] = ''

        self._add_output()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['value'] = args[0]

        widget = self.frame.contents[0].Widget
        widget.set_data(args[0])

        self.frame.do_execute(backward = False)

    def do_save(self) -> str:
        """"""
        return self.frame.data['value']

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
        def get_data() -> str:
            """"""
            return self.frame.data['value']

        def set_data(value: str) -> None:
            """"""
            take_snapshot(self, self.set_data, value)

        entry = NodeEntry(title    = _('String'),
                          get_data = get_data,
                          set_data = set_data)
        socket_type = NodeSocketType.OUTPUT
        self.frame.add_content(widget      = entry,
                               socket_type = socket_type,
                               data_type   = str,
                               get_data    = get_data,
                               set_data    = set_data)