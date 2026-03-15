# action.py
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

class Action():

    def __init__(self,
                 owner: object = None,
                 coown: object = None,
                 ) ->   None:
        """"""
        self.owner = owner
        self.coown = coown
        self.group = None

    def do(self,
           undoable: bool = True,
           ) ->      bool:
        """"""
        return False

    def undo(self) -> bool:
        """"""
        return False

    def clean(self) -> bool:
        """"""
        return False

    def isduplicate(self,
                    action: 'Action',
                    ) ->    'bool':
        """"""
        return False
