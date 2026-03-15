# function.py
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

def throttle(seconds):
    """
    Decorator to limit a function call to once every `seconds` period.
    """
    __last_called = [0] # mutable list

    def decorator(func):
        """"""
        from functools import wraps
        from time      import time

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
