# label.py
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
from gi.repository import Pango

class NodeLabel(Gtk.Label):

    __gtype_name__ = 'NodeLabel'

    def __init__(self,
                 label:    str,
                 can_link: bool = False,
                 ) ->      None:
        """"""
        super().__init__(label     = label,
                         xalign    = 1.0,
                         ellipsize = Pango.EllipsizeMode.END)

        self.add_css_class('node-label')

        if can_link:
            self.set_xalign(0.0)
            self.add_css_class('after-socket')
            self.add_css_class('node-widget')