# history.py
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

from collections import deque

from .action import Action
from .utils import generate_uuid

class History():
    """"""

    def __init__(self) -> None:
        """"""
        self.undo_stack: deque[Action] = deque()
        self.redo_stack: deque[Action] = deque()

        self._freezing: bool = False
        self._grouping: bool = False
        self._group_id: str  = None

    @property
    def freezing(self) -> bool:
        """"""
        return self._freezing

    @freezing.setter
    def freezing(self,
                 value: bool,
                 ) ->   None:
        """"""
        self._freezing = value

    @property
    def grouping(self) -> bool:
        """"""
        return self._grouping

    @grouping.setter
    def grouping(self,
                 value: bool,
                 ) ->   None:
        """"""
        self._grouping = value
        self._group_id = None

        if value:
            self._group_id = generate_uuid()

    def do(self,
           action:   Action,
           undoable: bool = True,
           add_only: bool = False,
           ) ->      bool:
        """"""
        action.group = self._group_id

        if self.undo_stack:
            last_action = self.undo_stack[-1]
            if action.isduplicate(last_action):
                return False

        def do_stack(action: Action) -> None:
            """"""
            # TODO: limit the stack size?
            self.undo_stack.append(action)
            for action in self.redo_stack:
                action.clean()
            self.redo_stack.clear()

        if add_only:
            do_stack(action)
            return True

        if action.do(undoable):
            if self._freezing:
                return True

            if undoable:
                do_stack(action)

            return True

        return False

    def undo(self) -> tuple[bool, list[Action]]:
        """"""
        actions = []

        if len(self.undo_stack) == 0:
            return (True, actions)

        action = self.undo_stack.pop()

        if not action.undo():
            return (False, actions)

        action.clean()
        actions.append(action)
        self.redo_stack.append(action)

        if not (group := action.group):
            return (True, actions)

        while True:
            if len(self.undo_stack) == 0:
                return (True, actions)

            action = self.undo_stack[-1]

            if action.group != group:
                return (True, actions)

            action = self.undo_stack.pop()

            if not action.undo():
                return (False, actions)

            action.clean()
            actions.append(action)
            self.redo_stack.append(action)

    def redo(self) -> tuple[bool, list[Action]]:
        """"""
        actions = []

        if len(self.redo_stack) == 0:
            return (True, actions)

        action = self.redo_stack.pop()

        if not action.do():
            return (False, actions)

        actions.append(action)
        self.undo_stack.append(action)

        if not (group := action.group):
            return (True, actions)

        while True:
            if len(self.redo_stack) == 0:
                return (True, actions)

            action = self.redo_stack[-1]

            if action.group != group:
                return (True, actions)

            action = self.redo_stack.pop()

            if not action.do():
                return (False, actions)

            actions.append(action)
            self.undo_stack.append(action)

            if len(self.redo_stack) == 0:
                return (True, actions)
