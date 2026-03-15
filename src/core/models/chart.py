# chart.py
#
# Copyright (c) 2025 Naufan Rusyda Faikar <hello@naruaika.me>
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

from enum  import Enum
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
