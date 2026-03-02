# link.py
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

from .socket import NodeSocket

class NodeLink():

    def __init__(self,
                 in_socket:  NodeSocket,
                 out_socket: NodeSocket,
                 compatible: bool = True,
                 ) ->        None:
        """"""
        self.in_socket  = in_socket
        self.out_socket = out_socket
        self.compatible = compatible

    def link(self) -> 'NodeLink':
        """"""
        self.in_socket.links.append(self)
        self.out_socket.links.append(self)

        self.in_socket.Content.do_link(self.out_socket, self.in_socket.Content)
        self.out_socket.Content.do_link(self.in_socket, self.out_socket.Content)
        # Implementors should manually prevent the workflow from being processed
        # twice or recursively at worst.

        return self

    def unlink(self) -> 'NodeLink':
        """"""
        in_socket = self.in_socket
        out_socket = self.out_socket

        in_socket.links.remove(self)
        out_socket.links.remove(self)

        in_socket.Content.do_unlink(in_socket)
        out_socket.Content.do_unlink(out_socket)

        return self
