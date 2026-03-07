# decimal.py
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

import logging

from ._template import NodeTemplate
from ._utils import take_snapshot

from ..frame import NodeFrame
from ..socket import NodeSocketType
from ..widgets import NodeEntry

logger = logging.getLogger(__name__)

class NodeDecimal(NodeTemplate):

    ndname = _('Decimal')

    action = 'new-decimal'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeDecimal(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['value'] = 0.0

        self._add_output()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        self.frame.data['value'] = args[0]

        widget = self.frame.contents[0].Widget
        widget.set_data(args[0])

        self.frame.do_execute(backward = False)

    def do_save(self) -> float:
        """"""
        return self.frame.data['value']

    def do_restore(self,
                   value: float,
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
        def get_data() -> float:
            """"""
            return self.frame.data['value']

        def set_data(value: float) -> None:
            """"""
            take_snapshot(self, self.set_data, value)

        spin = NodeEntry(title    = _('Decimal'),
                         get_data = get_data,
                         set_data = set_data)
        socket_type = NodeSocketType.OUTPUT
        self.frame.add_content(widget      = spin,
                               socket_type = socket_type,
                               data_type   = float,
                               get_data    = get_data,
                               set_data    = set_data)