# file_manager.py
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

from polars import DataFrame
from typing import Any
import json

class FileManager():

    @staticmethod
    def read_file(file_path: str,
                  **kwargs:  dict,
                  ) ->       Any:
        """"""
        from .utils import get_file_format
        file_format = get_file_format(file_path)
        file_format = file_format or 'csv'

        if file_format == 'wibook':
            try:
                with open(file_path) as file:
                    content = json.load(file)
                    return content
            except:
                pass
            return None

        sample_size = kwargs.get('sample_size', -1)
        u_kwargs    = kwargs.get('u_kwargs',    None)
        eager_load  = kwargs.get('eager_load',  False)

        if 'sample_size' in kwargs:
            del kwargs['sample_size']
        if 'u_kwargs' in kwargs:
            del kwargs['u_kwargs']
        if 'eager_load' in kwargs:
            del kwargs['eager_load']

#       from fastexcel import read_excel
        from polars import read_csv
        from polars import read_json
        from polars import read_parquet
        from polars import scan_csv
        from polars import scan_parquet
        read_methods = {
            'json':    read_json,
            'parquet': read_parquet if eager_load else scan_parquet,
            'csv':     read_csv     if eager_load else scan_csv,
            'tsv':     read_csv     if eager_load else scan_csv,
            'txt':     read_csv     if eager_load else scan_csv,
#           'xls':     read_excel,
#           'xlsx':    read_excel,
#           'xlsm':    read_excel,
#           'xlsb':    read_excel,
#           'xla':     read_excel,
#           'xlam':    read_excel,
#           'ods':     read_excel,
        }

        if file_format not in read_methods:
            return None

        read_method = read_methods[file_format]

        if u_kwargs is None:
            u_kwargs = {}

        # Grab all the default arguments from selected read method
        import inspect
        signature = inspect.signature(read_method)
        for name, param in signature.parameters.items():
            if param.default is not inspect.Parameter.empty:
                u_kwargs[name] = param.default

        if sample_size > 0:
            if file_format in {'parquet', 'csv', 'tsv', 'txt'}:
                if 'n_rows' in kwargs:
                    kwargs['n_rows'] = kwargs['n_rows'] or 0
                    kwargs['n_rows'] = min(sample_size, kwargs['n_rows'])
                    kwargs['n_rows'] = kwargs['n_rows'] or sample_size
                else:
                    kwargs['n_rows'] = sample_size

        if file_format == 'tsv':
            kwargs['separator'] = '\t'

        columns = []

        if read_method in {scan_csv, scan_parquet}:
            if 'columns' in kwargs:
                columns = kwargs.pop('columns')

        has_error = False

        try:
            u_kwargs.update(kwargs.copy())
            result = read_method(file_path, **kwargs)
        except:
            has_error = True

        if has_error:
            # Unless it's a text file, we won't retry
            # to read the file after the last failure
            if file_format not in {'csv', 'tsv', 'txt'}:
                return None

        if has_error:
            # Retry by ignoring any errors
            kwargs['ignore_errors'] = True
            kwargs['infer_schema'] = False
            u_kwargs.update(kwargs.copy())

            try:
                result = read_method(file_path, **kwargs)
                has_error = False
            except:
                pass # TODO: show errors to user?

        if has_error:
            # We use non-standard parameters to force loading the entire file contents
            # into one column without losing any data. This is an opinionated solution
            # indeed. But anyway, let's the user decide what to do next.
            kwargs['separator'] = '\x1f'
            kwargs['truncate_ragged_lines'] = True
            kwargs['quote_char'] = None
            u_kwargs.update(kwargs.copy())

            try:
                result = read_method(file_path, **kwargs)
                has_error = False
            except:
                pass # TODO: show errors to user?

        if has_error:
            return None

        if isinstance(result, DataFrame):
            result = result.lazy()

        if columns:
            result = result.select(columns)

        return result

    @staticmethod
    def write_file(file_path: str,
                   content:   Any,
                   **kwargs:  dict,
                   ) ->       bool:
        """"""
        from .utils import get_file_format
        file_format = get_file_format(file_path)
        file_format = file_format or 'csv'

        if file_format == 'wibook':
            try:
                with open(file_path, 'w') as file:
                    json.dump(content, file, indent = 4)
                    return True
            except:
                pass
            return False

        return False # TODO
