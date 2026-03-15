# link.py
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
