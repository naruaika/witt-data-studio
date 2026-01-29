# history.py
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
