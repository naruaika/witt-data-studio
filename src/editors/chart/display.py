# display.py
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

class ChartDisplay():

    CANVAS_PADDING = 10

    CHART_HEIGHT:     float = 500
    CHART_WIDTH:      float = 500
    CHART_MIN_HEIGHT: float = 150
    CHART_MIN_WIDTH:  float = 150

    AXIS_SIZE:     float = 50
    AXIS_MIN_SIZE: float = 30

    ICON_SIZE: float = 16
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
