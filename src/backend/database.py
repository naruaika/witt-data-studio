# database.py
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

from duckdb import connect
from typing import Any
from typing import Literal
from typing import TypeAlias
import logging

from .. import environment as env

logger = logging.getLogger(__name__)

class Database():

    Dialect: TypeAlias = Literal['mysql',
                                 'postgresql',
                                 'sqlite',
                                 'duckdb']

    @staticmethod
    def execute(dialect:   Dialect,
                config:    dict,
                query:     str,
                n_samples: int = -1,
                ) ->       tuple:
        """"""
        logger.info(f'Executing database query: {query}')

        connection = connect()

        success   = False
        message   = None
        file_path = None

        from time import time
        start_at = time()

        try:
            cschema = Database.get_schema(dialect, config)
            logger.info(f'Using database schema: {cschema}')

            connection.execute(cschema['curl'])

            if env.debug:
                kwargs = "level='debug', storage='stdout'"
                connection.execute(f'CALL enable_logging({kwargs});')

            start_at = time()

            if n_samples > 0:
                if output := connection.sql(query):
                    output = output.pl(lazy = True)
                    output = output.head(n_samples)
                    output = output.collect()

            else:
                if output := connection.sql(query):
                    from polars import scan_parquet
                    from tempfile import NamedTemporaryFile

                    kwargs = {'suffix': '.wisnap', 'delete': False}
                    with NamedTemporaryFile(**kwargs) as temp_file:
                        file_path = temp_file.name

                        output.pl(lazy = True).sink_parquet(file_path)
                        output = scan_parquet(file_path)

                        logger.debug(f'Created temporary file: {file_path}')

            executed = time()
            duration = executed - start_at
            success  = True

        except Exception as e:
            executed = time()
            duration = executed - start_at
            output   = message
            message  = str(e).strip('\n')

            logger.error(e, exc_info = True)

        finally:
            connection.close()

        log_info = {
            'query':    query,
            'success':  success,
            'message':  message,
            'duration': duration,
            'executed': executed,
            'fpath':    file_path,
            'cname':    config.get('alias'),
            'dbase':    config.get('database'),
        }

        logger.info(f'Query executed: {query}')

        logger.debug(f'With output: {output}')

        return output, log_info

    @staticmethod
    def check_connection(dialect: Dialect,
                         config:  dict,
                         ) ->     tuple:
        """"""
        logger.info(f'Checking database connection...')

        connection = connect()

        try:
            cschema = Database.get_schema(dialect, config)
            logger.info(f'Using database schema: {cschema}')

            if dialect == 'sqlite':
                import sqlite3
                sqlite3.connect(cschema['dbase'])

            connection.execute(cschema['curl'])

        except Exception as e:
            logger.error(e, exc_info = True)

            message = _("An error has occurred.")
            e = str(e)

            if "Access denied for user" in e:
                message = _("Invalid credentials.")
            if "no password supplied" in e:
                message = _("Invalid credentials.")
            if "authentication failed" in e:
                message = _("Invalid credentials.")
            if "Can't connect to" in e:
                message = _("Server unreachable.")
            if "Too many connections" in e:
                message = _("Server is busy.")
            if "of many connection errors" in e:
                message = _("Too many failed attempts.")
            if "Bad handshake" in e:
                message = _("Connection security error.")
            if "Is the server running" in e:
                message = _("Server is offline.")
            if "Unknown database" in e:
                message = _("Invalid database.")

            connection.close()

            return False, message

        finally:
            connection.close()

        logger.info(f'Connected to database: {config["alias"]}')

        return True, _("Successfully connected.")

    @staticmethod
    def get_schema(dialect: Dialect,
                   config:  dict,
                   ) ->     dict:
        """"""
        def quote_value(value: Any) -> str:
            """"""
            if value is None:
                return None
            value = str(value)
            value = value.replace("'", "''")
            value = value.replace('"', '\\"')
            return f'"{value}"'

        def build_kv_string(params: dict) -> str:
            """"""
            parts = []
            for key, value in params.items():
                if value is None:
                    continue
                value = quote_value(value)
                parts.append(f'{key}={value}')
            return ' '.join(parts)

        cname    = config.get('alias')    or _('New Connection')
        readonly = config.get('readonly') or True

        match dialect:
            case 'mysql':
                params = {
                    'host':   config.get('host')     or 'localhost',
                    'port':   config.get('port')     or '3306',
                    'user':   config.get('username') or 'root',
                    'passwd': config.get('password') or None,
                    'db':     config.get('database') or None,
                }
                curl = (
                    f"ATTACH '{build_kv_string(params)}' AS \"{cname}\" "
                    f"(TYPE mysql{', READ_ONLY' if readonly else ''});"
                )
                return {
                    'ctype': 'mysql',
                    'cname': cname,
                    'curl':  curl,
                }

            case 'postgresql':
                params = {
                    'host':   config.get('host')     or 'localhost',
                    'port':   config.get('port')     or '5432',
                    'user':   config.get('username') or 'postgres',
                    'passwd': config.get('password') or None,
                    'db':     config.get('database') or None,
                }
                curl = (
                    f"ATTACH '{build_kv_string(params)}' AS \"{cname}\" "
                    f"(TYPE postgresql{', READ_ONLY' if readonly else ''});"
                )
                return {
                    'ctype': 'postgresql',
                    'cname': cname,
                    'curl':  curl,
                }

            case 'sqlite':
                dbase = config.get('database') or '~/sample.db'
                curl = (
                    f"ATTACH '{dbase}' AS \"{cname}\" "
                    f"(TYPE sqlite{', READ_ONLY' if readonly else ''});"
                )
                return {
                    'ctype': 'sqlite',
                    'cname': cname,
                    'curl':  curl,
                    'dbase': dbase,
                }

            case 'duckdb':
                dbase = config.get('database') or '~/sample.duckdb'
                curl = (
                    f"ATTACH '{dbase}' AS \"{cname}\" "
                    f"(TYPE duckdb{', READ_ONLY' if readonly else ''});"
                )
                return {
                    'ctype': 'duckdb',
                    'cname': cname,
                    'curl':  curl,
                    'dbase': dbase,
                }

        raise Exception(f'Unknown dialect: {dialect}')

    @staticmethod
    def hash_config(config: dict) -> str:
        """"""
        logging.debug(f'Hashing database config: {config}')

        from hashlib import sha256
        from json import dumps

        result = {
            'dialect':  config.get('dialect'),
            'host':     config.get('host'),
            'port':     config.get('port'),
            'database': config.get('database'),
            'username': config.get('username'),
        }
        result = dumps(result)
        result = result.encode('utf-8')
        result = sha256(result).hexdigest()

        logging.debug(f'Hashed database config: {result}')

        return result
