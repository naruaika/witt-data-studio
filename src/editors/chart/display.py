# display.py
#
# Copyright 2025 Naufan Rusyda Faikar <hello@naruaika.me>
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

class ChartDisplay():

    CANVAS_PADDING = 10

    CHART_HEIGHT:     float = 500
    CHART_WIDTH:      float = 500
    CHART_MIN_HEIGHT: float = 150
    CHART_MIN_WIDTH:  float = 150

    AXIS_SIZE:     float = 50
    AXIS_MIN_SIZE: float = 30

    ICON_SIZE: float = 18
    FONT_SIZE: float = 12

    BAR_CHART_BAR_SIZE:        float = 40
    BAR_CHART_BAR_SPACING:     float = 20
    BAR_CHART_BAR_MIN_SIZE:    float = 25
    BAR_CHART_BAR_MIN_SPACING: float = 10

    TIMELINE_BAR_MIN_SIZE:    float = 5
    TIMELINE_BAR_MIN_SPACING: float = 5

    pan_increment:    int = 0.05
    scroll_increment: int = 20
    page_increment:   int = 20

    scroll_y_position: int = 0
    scroll_x_position: int = 0
