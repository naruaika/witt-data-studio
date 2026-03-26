# filter_rows.py
#
# Copyright 2025 Naufan Rusyda Faikar <hello@naruaika.me>
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

from datetime      import datetime
from datetime      import timedelta
from gi.repository import GObject
from gi.repository import Gtk
from polars        import DataFrame
from polars        import LazyFrame

import logging

from ._template import NodeTemplate
from ._utils    import isdatatable
from ._utils    import take_snapshot
from ._utils    import serialize_data
from ._utils    import deserialize_data

from ..content import NodeContent
from ..frame   import NodeFrame
from ..socket  import NodeSocket
from ..socket  import NodeSocketType
from ..widgets import NodeFilterBuilder
from ..widgets import NodeLabel

logger = logging.getLogger(__name__)

class NodeFilterRows(NodeTemplate):

    ndname = _('Filter Rows')

    action = 'filter-rows'

    @staticmethod
    def new(x:   int = 0,
            y:   int = 0,
            ) -> NodeFrame:
        """"""
        self = NodeFilterRows(x, y)

        self.frame.set_data   = self.set_data
        self.frame.do_process = self.do_process
        self.frame.do_save    = self.do_save
        self.frame.do_restore = self.do_restore

        self.frame.data['all-columns']     = []
        self.frame.data['clauses']         = []
        self.frame.data['refresh-clauses'] = True
        self.frame.data['clause.exp']      = False

        self._add_output()
        self._add_input()

        return self.frame

    def set_data(self, *args, **kwargs) -> None:
        """"""
        if isinstance(args, tuple):
            args = list(args)
        self.frame.data['clauses'] = args
        self.frame.data['refresh-clauses'] = True
        self.frame.do_execute(backward = False)

    def do_process(self,
                   pair_socket:  NodeSocket,
                   self_content: NodeContent,
                   ) ->          None:
        """"""
        self_content = self.frame.contents[1]

        if not (links := self_content.Socket.links):
            self.frame.data['table'] = DataFrame()
            self._refresh_selector()
            return

        pair_content = links[0].in_socket.Content
        table = pair_content.get_data()

        if not isdatatable(table):
            self.frame.data['table'] = DataFrame()
            self._refresh_selector()
            return

        self.frame.data['table'] = table
        self._refresh_selector()

        if self.frame.data['all-columns']:
            if clauses := self.frame.data['clauses']:
                table = self._build_filter_expr(table, clauses)

        self.frame.data['table'] = table

    def _build_filter_expr(self,
                           table:   LazyFrame,
                           clauses: list,
                           ) ->     LazyFrame:
        """"""
        if not clauses:
            return table

        expr = None

        for clause in clauses:
            operator = clause[0]

            _expr = self._build_expression(clause)

            if expr is None:
                expr = _expr
                continue
            if operator == 'and':
                expr = expr & _expr
                continue
            if operator == 'or':
                expr = expr | _expr
                continue

            raise ValueError()

        return table.filter(expr)

    def _build_expression(self,
                          clause: list,
                          ) ->    None:
        """"""
        from polars import col

        _, column, operator, *values = clause

        expr = col(column)

        if operator == 'is-null':
            return expr.is_null()

        if operator == 'is-not-null':
            return expr.is_not_null()

        if operator == 'equals':
            if values[0] is None:
                return expr.is_null()
            return expr == values[0]

        if operator == 'does-not-equal':
            if values[0] is None:
                return expr.is_not_null()
            return expr != values[0]

        if operator == 'begins-with':
            return expr.str.starts_with(values[0])

        if operator == 'does-not-begin-with':
            return expr.str.starts_with(values[0]).not_()

        if operator == 'ends-with':
            return expr.str.ends_with(values[0])

        if operator == 'does-not-end-with':
            return expr.str.ends_with(values[0]).not_()

        if operator == 'contains':
            return expr.str.contains(values[0], literal = True)

        if operator == 'does-not-contain':
            return expr.str.contains(values[0], literal = True).not_()

        if operator in {'is-greater-than',
                        'is-after'}:
            return expr > values[0]

        if operator in {'is-greater-than-or-equal-to',
                        'is-after-or-equal-to'}:
            return expr >= values[0]

        if operator in {'is-less-than',
                        'is-before'}:
            return expr < values[0]

        if operator in {'is-less-than-or-equal-to',
                        'is-before-or-equal-to'}:
            return expr <= values[0]

        if operator == 'is-between':
            return expr.is_between(values[0], values[1])

        if operator == 'is-not-between':
            return expr.is_between(values[0], values[1]).not_()

        if operator == 'above-average':
            return expr > expr.mean()

        if operator == 'below-average':
            return expr < expr.mean()

        if operator == 'is-earliest':
            return expr == expr.min()

        if operator == 'is-latest':
            return expr == expr.max()

        if operator == 'is-not-earliest':
            return expr != expr.min()

        if operator == 'is-not-latest':
            return expr != expr.max()

        now = datetime.now()

        if operator == 'is-in-the-next':
            amount, unit = values
            start, end = self._relative_period_bounds(now, amount, unit, 'next')
            return expr.is_between(start, end)

        if operator == 'is-in-the-previous':
            amount, unit = values
            start, end = self._relative_period_bounds(now, amount, unit, 'previous')
            return expr.is_between(start, end)

        if operator == 'is-in-year':
            start, end = self._year_bounds(now, values[0])
            return expr.is_between(start, end)

        if operator == 'is-in-quarter':
            value = values[0]

            if value.startswith('quarter-'):
                q = int(value.split('-')[1])
                return ((expr.dt.month() - 1) // 3 + 1) == q

            start, end = self._quarter_bounds(now, value)
            return expr.is_between(start, end)

        if operator == 'is-in-month':
            value = values[0]

            if value in {'last-month',
                         'this-month',
                         'next-month'}:
                start, end = self._month_bounds(now, value)
                return expr.is_between(start, end)

            mapping = {
                'january':   1,
                'february':  2,
                'march':     3,
                'april':     4,
                'may':       5,
                'june':      6,
                'july':      7,
                'august':    8,
                'september': 9,
                'october':   10,
                'november':  11,
                'december':  12,
            }

            if value in mapping:
                return expr.dt.month() == mapping[value]

        if operator == 'is-in-week':
            start, end = self._week_bounds(now, values[0])
            return expr.is_between(start, end)

        if operator == 'is-in-day':
            start, end = self._day_bounds(now, values[0])
            return expr.is_between(start, end)

        raise ValueError()

    def _relative_period_bounds(self,
                                now:       datetime,
                                amount:    int,
                                unit:      str,
                                direction: str,
                                ) ->       timedelta:
        """"""
        if unit == 'years':
            year = now.year

            if direction == 'next':
                start_year = year + 1
                end_year   = year + amount
            else:
                start_year = year - amount
                end_year   = year - 1

            start = datetime(start_year, 1, 1)
            end   = datetime(end_year, 12, 31, 23, 59, 59, 999999)
            return start, end

        if unit == 'quarters':
            quarter = (now.month - 1) // 3 + 1

            if direction == 'next':
                q_start = quarter + 1
                q_end   = quarter + amount
            else:
                q_start = quarter - amount
                q_end   = quarter - 1

            start_year = now.year
            while q_start <= 0:
                q_start += 4
                start_year -= 1
            while q_start > 4:
                q_start -= 4
                start_year += 1

            end_year = start_year
            while q_end <= 0:
                q_end += 4
                end_year -= 1
            while q_end > 4:
                q_end -= 4
                end_year += 1

            start_month = (q_start - 1) * 3 + 1
            end_month   = (q_end   - 1) * 3 + 3

            from calendar import monthrange

            end_day = monthrange(end_year, end_month)[1]
            start   = datetime(start_year, start_month, 1)
            end     = datetime(end_year, end_month, end_day, 23, 59, 59, 999999)
            return start, end

        if unit == 'months':
            if direction == 'next':
                start_offset = 1
                end_offset   = amount
            else:
                start_offset = -amount
                end_offset   = -1

            def add_months(dt:     datetime,
                           offset: int,
                           ) ->    datetime:
                """"""
                year = dt.year + (dt.month - 1 + offset) // 12
                month = (dt.month - 1 + offset) % 12 + 1
                return datetime(year, month, 1)

            from calendar import monthrange

            end_month = add_months(now.replace(day = 1), end_offset)
            end_day   = monthrange(end_month.year, end_month.month)[1]
            start     = add_months(now.replace(day = 1), start_offset)
            end       = datetime(end_month.year, end_month.month, end_day, 23, 59, 59, 999999)
            return start, end

        if unit == 'weeks':
            current_week_start = now - timedelta(days = now.weekday())

            if direction == 'next':
                start = current_week_start + timedelta(weeks = 1)
                end   = current_week_start + timedelta(weeks = amount)
            else:
                start = current_week_start - timedelta(weeks = amount)
                end   = current_week_start - timedelta(weeks = 1)

            start = start.replace(hour        = 0,
                                  minute      = 0,
                                  second      = 0,
                                  microsecond = 0)
            end = end + timedelta(days         = 6,
                                  hours        = 23,
                                  minutes      = 59,
                                  seconds      = 59,
                                  microseconds = 999999)
            return start, end

        mapping = {
            'days':    timedelta(days    = amount),
            'hours':   timedelta(hours   = amount),
            'minutes': timedelta(minutes = amount),
            'seconds': timedelta(seconds = amount),
        }

        if unit not in mapping:
            unit = 'days'
        delta = mapping[unit]

        if direction == 'next':
            return now, now + delta
        else:
            return now - delta, now

    def _year_bounds(self,
                     now:   datetime,
                     value: str,
                     ) ->   tuple:
        """"""
        if value == 'this-year':
            return (self._start_of_year(now), self._end_of_year(now))

        if value == 'last-year':
            dt = now.replace(year = now.year - 1)
            return (self._start_of_year(dt), self._end_of_year(dt))

        if value == 'next-year':
            dt = now.replace(year = now.year + 1)
            return (self._start_of_year(dt), self._end_of_year(dt))

        if value == 'year-to-date':
            return (self._start_of_year(now), now)

    def _quarter_bounds(self,
                        now:   datetime,
                        value: str,
                        ) ->   tuple:
        """"""
        current = (now.month - 1) // 3 + 1

        def bounds(year:    int,
                   quarter: int,
                   ) ->     tuple:
            """"""
            start_month = (quarter - 1) * 3 + 1
            start = datetime(year, start_month, 1)

            if quarter == 4:
                end = datetime(year, 12, 31, 23, 59, 59, 999999)
            else:
                end = datetime(year, start_month + 3, 1) - timedelta(microseconds = 1)

            return start, end

        if value == 'this-quarter':
            return bounds(now.year, current)

        if value == 'last-quarter':
            quarter = current - 1 or 4
            year = now.year - 1 if current == 1 else now.year
            return bounds(year, quarter)

        if value == 'next-quarter':
            quarter = current + 1 if current < 4 else 1
            year = now.year + 1 if current == 4 else now.year
            return bounds(year, quarter)

    def _month_bounds(self,
                      now:   datetime,
                      value: str,
                      ) ->   tuple:
        """"""
        dt = now
        if value == 'last-month':
            dt = (now.replace(day = 1) - timedelta(days = 1))
        if value == 'next-month':
            dt = (now.replace(day = 28) + timedelta(days = 4))
            dt = dt.replace(day = 1)
        return self._start_of_month(dt), self._end_of_month(dt)

    def _week_bounds(self,
                     now:   datetime,
                     value: str,
                     ) ->   tuple:
        """"""
        dt = now
        if value == 'last-week':
            dt = now - timedelta(weeks = 1)
        if value == 'next-week':
            dt = now + timedelta(weeks = 1)
        return self._start_of_week(dt), self._end_of_week(dt)

    def _day_bounds(self,
                    now:   datetime,
                    value: str,
                    ) ->   tuple:
        """"""
        dt = now
        if value == 'yesterday':
            dt = now - timedelta(days = 1)
        if value == 'tomorrow':
            dt = now + timedelta(days = 1)
        start = datetime(dt.year, dt.month, dt.day)
        end = start + timedelta(days = 1) - timedelta(microseconds = 1)
        return start, end

    def _start_of_year(self,
                       dt:  datetime,
                       ) -> datetime:
        """"""
        return datetime(dt.year, 1, 1)

    def _end_of_year(self,
                     dt:  datetime,
                     ) -> datetime:
        """"""
        return datetime(dt.year, 12, 31, 23, 59, 59, 999999)

    def _start_of_month(self,
                        dt:  datetime,
                        ) -> datetime:
        """"""
        return datetime(dt.year, dt.month, 1)

    def _end_of_month(self,
                      dt:  datetime,
                      ) -> datetime:
        """"""
        from calendar import monthrange
        last_day = monthrange(dt.year, dt.month)[1]
        return datetime(dt.year, dt.month, last_day, 23, 59, 59, 999999)

    def _start_of_week(self,
                       dt:  datetime,
                       ) -> datetime:
        """"""
        start = dt - timedelta(days = dt.weekday())
        return datetime(start.year, start.month, start.day)

    def _end_of_week(self,
                     dt:  datetime,
                     ) -> datetime:
        """"""
        start = self._start_of_week(dt)
        end = start + timedelta(days = 6)
        return datetime(end.year, end.month, end.day, 23, 59, 59, 999999)

    def do_save(self) -> list:
        """"""
        return serialize_data(self.frame.data['clauses'])

    def do_restore(self,
                   value: list,
                   ) ->   None:
        """"""
        try:
            self.set_data(*deserialize_data(value))
        except Exception as e:
            logger.error(e, exc_info = True)
            self.frame.ErrorButton.set_tooltip_text(str(e))
            self.frame.ErrorButton.set_visible(True)
        else:
            self.frame.ErrorButton.set_visible(False)

    def _add_output(self) -> None:
        """"""
        self.frame.data['table'] = DataFrame()

        def get_data() -> DataFrame:
            """"""
            return self.frame.data['table']

        def set_data(value: DataFrame) -> None:
            """"""
            self.frame.data['table'] = value
            self.frame.do_execute(backward = False)

        widget = NodeLabel(_('Table'))
        socket_type = NodeSocketType.OUTPUT
        self.frame.add_content(widget      = widget,
                               socket_type = socket_type,
                               data_type   = DataFrame,
                               get_data    = get_data,
                               set_data    = set_data)

    def _add_input(self) -> None:
        """"""
        label = NodeLabel(_('Table'), can_link = True)
        socket_type = NodeSocketType.INPUT
        self.frame.add_content(widget      = label,
                               socket_type = socket_type,
                               data_type   = DataFrame)

    def _refresh_selector(self) -> None:
        """"""
        table = self.frame.data['table']

        table_columns = table.collect_schema().names()

        # Filter unvalid clauses from selection
        if table_columns:
            if self.frame.data['clauses']:
                clauses = []
                for clause in self.frame.data['clauses']:
                    column = clause[1]
                    if column in table_columns:
                        clauses.append(clause)
                self.frame.data['clauses'] = clauses

        if self.frame.data['all-columns'] != table_columns:
            self.frame.data['refresh-clauses'] = True

        self.frame.data['all-columns'] = table_columns

        if self.frame.data['refresh-clauses']:
            if len(self.frame.contents) == 3:
                content = self.frame.contents[-1]
                self.frame.remove_content(content)
            if table_columns:
                self._add_selector()

        if not self.frame.data['clauses']:
            self.frame.data['clause.exp'] = True

        if self.frame.data['clause.exp']:
            if len(self.frame.contents) == 3:
                widget = self.frame.contents[-1].Widget
                widget.set_expanded(True)

        self.frame.data['refresh-clauses'] = False

    def _add_selector(self) -> None:
        """"""
        def get_data() -> list:
            """"""
            return self.frame.data['clauses']

        def set_data(value: list) -> None:
            """"""
            if self.frame.data['clauses'] == value:
                return
            def callback(value: list) -> None:
                """"""
                self.frame.data['clauses'] = value
                self.frame.do_execute(backward = False)
            take_snapshot(self, callback, value)

        table = self.frame.data['table']
        tschema = table.collect_schema()

        widget = NodeFilterBuilder(get_data = get_data,
                                   set_data = set_data,
                                   tschema  = tschema)
        expander = Gtk.Expander(label = _('Clauses'),
                                child = widget)
        self.frame.add_content(expander)

        def on_expanded(widget:     Gtk.Widget,
                        param_spec: GObject.ParamSpec,
                        ) ->        None:
            """"""
            self.frame.data['clause.exp'] = widget.get_expanded()

        expander.connect('notify::expanded', on_expanded)