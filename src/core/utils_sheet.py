# utils_sheet.py
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

from typing import TypeAlias

FilePath:   TypeAlias = str
SheetName:  TypeAlias = str
TableName:  TypeAlias = str
ColumnName: TypeAlias = str
RangeName:  TypeAlias = str

STableRef:  TypeAlias = tuple[FilePath, SheetName, TableName, ColumnName]
SRangeRef:  TypeAlias = tuple[FilePath, SheetName, RangeName]

def parse_table_rpath(tpath: str) -> STableRef:
    """"""
    import re

    pattern = re.compile(r"""
        ^
        (?P<path_container>
            (?:
                @
                |
                (['"])(.*?)\2
            )
            :
        )?
        (?P<sheet_container>
            (?P<sheet_name>
                (?:
                    (['"])(.*?)\6
                    |
                    [^'!:"\[\]]+
                )
            )
            !
        )?
        (?P<table_container>
            (?P<table_name>
                (?:
                    (['"])(.*?)\10
                    |
                    [^'!:"\[\]]+
                )
            )
        )?
        (?P<column_container>
            \[
            (?P<column_name>[^\]]+)
            \]
        )?
        $
    """, re.VERBOSE)

    result = {
        'file_path'   : None,
        'sheet_name'  : None,
        'table_name'  : None,
        'column_name' : None,
    }

    if not (match := pattern.match(tpath)):
        return tuple(result.values())

    def clean_quotes(value) -> str:
        """"""
        if not value:
            return None
        value = value.strip()
        if (
            (value.startswith("'") and value.endswith("'")) or
            (value.startswith('"') and value.endswith('"'))
        ):
            return value[1:-1]
        return value

    # File Path
    if path_group := match.group('path_container'):
        path_content = path_group.rstrip(':')
        result['file_path'] = None if path_content == '@' \
                                   else clean_quotes(path_content)

    # Sheet Name
    if sheet_name := match.group('sheet_name'):
        result['sheet_name'] = None if sheet_name == '@' \
                                    else clean_quotes(sheet_name)

    # Table Name
    if table_name := match.group('table_name'):
        result['table_name'] = None if table_name == '@' \
                                    else clean_quotes(table_name)

    # Column Name
    if column_name := match.group('column_name'):
        result['column_name'] = None if column_name == '@' \
                                     else clean_quotes(column_name)

    return tuple(result.values())