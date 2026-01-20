# document.py
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

class Document():

    # Should we move all data storage and processing
    # to a compiled language, i.e. Rust? We discourage
    # the users for applying expensive computation to
    # non-tabular data. But we cannot prevent them from
    # doing so and sometimes the users just don't aware.
    # Flag this as TODO for now.

    def __init__(self,
                 title: str = 'Document',
                 ) ->   None:
        """"""
        self.title = title

        self._undo_stack: deque[Action] = deque()
        self._redo_stack: deque[Action] = deque()

    def do(self,
           action:   Action,
           undoable: bool = True,
           ) ->      bool:
        """"""
        if action.do(undoable):
            if undoable:
                self._undo_stack.append(action)
                for action in self._redo_stack:
                    action.clean()
                self._redo_stack.clear()
            return True
        return False

    def undo(self) -> Action:
        """"""
        if len(self._undo_stack) == 0:
            return None
        action = self._undo_stack.pop()
        if not action.undo():
            return None
        action.clean()
        self._redo_stack.append(action)
        return action

    def redo(self) -> Action:
        """"""
        if len(self._redo_stack) == 0:
            return None
        action = self._redo_stack.pop()
        if not action.do():
            return None
        self._undo_stack.append(action)
        return action

    def has_data(self) -> bool:
        """"""
        return False
