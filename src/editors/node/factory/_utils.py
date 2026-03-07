# _utils.py
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

from ._template import NodeTemplate

from ....core.utils import isiterable

from ..content import NodeContent
from ..socket import NodeSocket

def iscompatible(pair_socket:  NodeSocket,
                 self_content: NodeContent,
                 ) ->          bool:
    """"""
    self_socket = self_content.Socket

    if (
        pair_socket.data_type == Any or
        self_socket.data_type == Any
    ):
        compatible = True
    else:
        pair_types = set(pair_socket.data_type) \
                     if isiterable(pair_socket.data_type) \
                     else {pair_socket.data_type}
        self_types = set(self_socket.data_type) \
                     if isiterable(self_socket.data_type) \
                     else {self_socket.data_type}
        compatible = not pair_types.isdisjoint(self_types)

    link = self_socket.links[0]
    link.compatible = compatible

    return compatible


def isreconnected(pair_socket:  NodeSocket,
                  self_content: NodeContent,
                  ) ->          bool:
    """"""
    incoming_node_uid = id(pair_socket.Frame)

    if self_content.node_uid == incoming_node_uid:
        return True

    self_content.node_uid = incoming_node_uid

    return False


def isdatatable(value: Any) -> bool:
    """"""
    from polars import DataFrame
    from polars import LazyFrame
    return isinstance(value, (DataFrame, LazyFrame))


def serialize_data(obj: Any) -> Any:
    """"""
    from datetime import datetime
    from datetime import date
    from datetime import time

    if isinstance(obj, datetime):
        return {
            '_type': 'datetime',
            'value': obj.isoformat()
        }

    if isinstance(obj, date):
        return {
            '_type': 'date',
            'value': obj.isoformat()
        }

    if isinstance(obj, time):
        return {
            '_type': 'time',
            'value': obj.isoformat()
        }

    if isinstance(obj, dict):
        return {
            key: serialize_data(value)
                 for key, value in obj.items()
        }

    if isiterable(obj):
        return [serialize_data(item) for item in obj]

    return obj


def deserialize_data(obj) -> Any:
    """"""
    from datetime import datetime
    from datetime import date
    from datetime import time

    if isinstance(obj, dict) and '_type' in obj:
        _type = obj['_type']
        value = obj['value']

        if _type == 'datetime':
            return datetime.fromisoformat(value)

        if _type == 'date':
            return date.fromisoformat(value)

        if _type == 'time':
            return time.fromisoformat(value)

        return obj

    if isinstance(obj, dict):
        return {
            key: deserialize_data(value)
                 for key, value in obj.items()
        }

    if isinstance(obj, list):
        return [deserialize_data(item) for item in obj]

    return obj


def take_snapshot(node:     NodeTemplate,
                  callback: callable,
                  *args:    list,
                  **kwargs: dict,
                  ) ->      None:
    """"""
    old_data = node.do_save()
    callback(*args, **kwargs)
    new_data = node.do_save()

    if not (editor := node.frame.get_editor()):
        return

    if not (window := editor.get_window()):
        return

    from ..actions import ActionEditNode
    values = (old_data, new_data)
    action = ActionEditNode(editor, node.frame, values)

    window.do(action, add_only = True)
