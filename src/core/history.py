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

    def __init__(self,
                 owner: str = 'global',
                 ) ->   None:
        """"""
        self._owner = owner

        self._undo_stack: deque[Action] = deque()
        self._redo_stack: deque[Action] = deque()

        self._freezing: bool    = False
        self._grouping: bool    = False
        self._group_id: str     = None
        self._co_owner: History = None

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

    @property
    def co_owner(self) -> 'History':
        """"""
        return self._co_owner

    @co_owner.setter
    def co_owner(self,
                 value: 'History',
                 ) ->   'None':
        """"""
        self._co_owner = value

    def do(self,
           action:   Action,
           undoable: bool = True,
           ) ->      bool:
        """"""
        action.group = self._group_id

        if action.do(undoable):
            if self._freezing:
                return True

            if undoable:
                self._undo_stack.append(action)
                for action in self._redo_stack:
                    action.clean()
                self._redo_stack.clear()

            return True

        # TODO: undo all previous actions with the same group ID

        return False

    def undo(self) -> list[Action]:
        """"""
        actions = []

        if len(self._undo_stack) == 0:
            return actions

        action = self._undo_stack.pop()

        if not action.undo():
            return actions

        action.clean()
        actions.append(action)
        self._redo_stack.append(action)

        if not (group := action.group):
            return actions

        while True:
            if len(self._undo_stack) == 0:
                return actions

            action = self._undo_stack[-1]

            if action.group != group:
                return actions

            action = self._undo_stack.pop()

            if not action.undo():
                return actions

            action.clean()
            actions.append(action)
            self._redo_stack.append(action)

    def redo(self) -> list[Action]:
        """"""
        actions = []

        if len(self._redo_stack) == 0:
            return actions

        action = self._redo_stack.pop()

        if not action.do():
            return actions

        actions.append(action)
        self._undo_stack.append(action)

        if not (group := action.group):
            return actions

        while True:
            if len(self._redo_stack) == 0:
                return actions

            action = self._redo_stack[-1]

            if action.group != group:
                return actions

            action = self._redo_stack.pop()

            if not action.do():
                return actions

            actions.append(action)
            self._undo_stack.append(action)

            if len(self._redo_stack) == 0:
                return actions
