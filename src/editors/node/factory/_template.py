# _template.py
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

from typing import Any

from ....core.utils import generate_uuid

from ..frame import NodeFrame

class NodeTemplate():

    ndname = _('Template')

    action = ''

    def __init__(self,
                 x:    int = 0,
                 y:    int = 0,
                 name: str = None,
                 ) ->  None:
        """"""
        if name:
            self.ndname = name

        self.frame = NodeFrame(title  = self.ndname,
                               x      = x,
                               y      = y,
                               parent = self)

        self.frame.data = {} # internal use only

    @staticmethod
    def new(cls: object,
            x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        return NodeFrame(cls.ndname, x, y)

    def clone(self) -> NodeFrame:
        """"""
        value = self.frame.do_save()
        frame = self.__class__.new(self.frame.x + 30,
                                   self.frame.y + 30)
        frame.do_restore(value)
        return frame

    def add_data(self,
                 value: Any,
                 ) ->   str:
        """"""
        uuid = generate_uuid()
        self.frame.data[uuid] = value
        return uuid
