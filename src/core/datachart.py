# datachart.py
#
# Copyright (c) 2025 Naufan Rusyda Faikar
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

from enum import Enum
from numpy import array as narray
from numpy import ndarray

class ChartType(Enum):

    BAR_CHART     = _('Bar Chart')     # 0
    LINE_CHART    = _('Line Chart')    # 1
    SCATTER_CHART = _('Scatter Chart') # 2



class ChartProps():

    def __init__(self,
                 x_data: ndarray = narray([]),
                 y_data: ndarray = narray([]),
                 ) ->    None:
        """"""
        self.x_data = x_data
        self.y_data = y_data

    def has_data(self) -> bool:
        """"""
        return len(self.x_data) > 0 and \
               len(self.y_data) > 0



class DataChart():

    def __init__(self,
                 cname:      str,
                 cschema:    dict       = {},
                 cprops:     ChartProps = None,
                 transposed: bool       = False,
                 ) ->        None:
        """"""
        self.cname      = cname
        self.cschema    = cschema
        self.cprops     = cprops or ChartProps()
        self.transposed = transposed
