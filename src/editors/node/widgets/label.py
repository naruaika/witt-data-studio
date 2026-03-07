# label.py
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