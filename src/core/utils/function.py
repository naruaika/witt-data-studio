# function.py
#
# Copyright (c) 2025 Naufan Rusyda Faikar <hello@naruaika.me>
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

def throttle(seconds):
    """
    Decorator to limit a function call to once every `seconds` period.
    """
    __last_called = [0] # mutable list

    def decorator(func):
        """"""
        from functools import wraps
        from time import time

        @wraps(func)
        def wrapper(*args, **kwargs):
            """"""
            elapsed = time() - __last_called[0]
            if elapsed >= seconds:
                __last_called[0] = time()
                return func(*args, **kwargs)

        return wrapper

    return decorator


def debounce(interval):
    """
    Decorator that will postpone a function's execution until
    after `interval` have elapsed since the last time it was invoked.
    """
    def decorator(func):
        """"""
        __timer = [None] # a mutable list
        __last_args = []
        __last_kwargs = {}

        from functools import wraps
        from threading import Timer

        @wraps(func)
        def wrapper(*args, **kwargs):
            """"""
            # Cancel the previous timer if it's still active
            if __timer[0] is not None and __timer[0].is_alive():
                __timer[0].cancel()

            # Store the current arguments for the final call
            __last_args[:] = args
            __last_kwargs.clear()
            __last_kwargs.update(kwargs)

            def execute():
                """"""
                return func(*__last_args, **__last_kwargs)

            # Create and start a new timer
            new_timer = Timer(interval, execute)
            new_timer.start()
            __timer[0] = new_timer

        return wrapper

    return decorator
