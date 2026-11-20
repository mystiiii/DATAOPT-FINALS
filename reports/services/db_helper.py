import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    """Raised when live SQL Server AdventureWorks connection or query fails."""
    pass


def _build_server(host, port):
    # Named instances (e.g. localhost\SQLEXPRESS) resolve via SQL Browser without a port.
    if port and '\\' not in host and ',' not in host:
        return f"{host},{port}"
    return host


def get_connection():
    """
    Connects to Microsoft SQL Server (AdventureWorks2019) using pyodbc,
    supporting Windows Authentication (SSMS) and SQL Server Authentication.
    Falls back to pymssql if pyodbc is not installed.
    """
    host = os.getenv('DB_HOST', 'localhost').strip()
    port = os.getenv('DB_PORT', '').strip()
    user = os.getenv('DB_USER', '').strip()
    password = os.getenv('DB_PASSWORD', '').strip()
    database = os.getenv('DB_NAME', 'AdventureWorks2019').strip()
    driver = os.getenv('DB_DRIVER', 'ODBC Driver 18 for SQL Server').strip()
    trust_cert = os.getenv('DB_TRUST_CERT', 'yes').strip()
    trusted_env = os.getenv('DB_TRUSTED_CONNECTION', '').strip().lower()
    use_trusted = trusted_env in ('yes', 'true', '1') or (not trusted_env and not user and not password)

    try:
        import pyodbc
    except ImportError:
        pyodbc = None

    if pyodbc is not None:
        server = _build_server(host, port)
        parts = [
            f"DRIVER={{{driver}}}",
            f"SERVER={server}",
            f"DATABASE={database}",
            f"TrustServerCertificate={trust_cert}",
        ]
        if use_trusted:
            parts.append("Trusted_Connection=yes")
        else:
            parts.append(f"UID={user}")
            parts.append(f"PWD={password}")
        conn_str = ";".join(parts)
        try:
            return pyodbc.connect(conn_str, timeout=3)
        except Exception as e:
            logger.error(f"Failed connecting to SQL Server at {server} ({database}) via pyodbc: {e}")
            raise DatabaseConnectionError(f"Cannot connect to SQL Server database '{database}' on {server}. Error: {e}")

    try:
        import pymssql
        connect_kwargs = {
            'server': host,
            'user': user,
            'password': password,
            'database': database,
            'timeout': 3,
            'login_timeout': 3,
        }
        if port:
            connect_kwargs['port'] = int(port)
        return pymssql.connect(**connect_kwargs)
    except Exception as e:
        target = f"{host}:{port}" if port else host
        logger.error(f"Failed connecting to SQL Server at {target} ({database}): {e}")
        raise DatabaseConnectionError(f"Cannot connect to SQL Server database '{database}' on {target}. Error: {e}")


def execute_query(sql, params=None):
    """
    Executes raw SQL query on live AdventureWorks2019 database.
    Strictly returns database results. Never falls back to mock data.
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            if not cursor.description:
                return []
            rows = cursor.fetchall()
            if rows and isinstance(rows[0], dict):
                return rows
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
    except DatabaseConnectionError:
        raise
    except Exception as e:
        logger.error(f"SQL execution failure: {e}")
        raise DatabaseConnectionError(f"Database Query Error: {e}")
    finally:
        if conn:
            conn.close()


def check_connection():
    """
    Quick check to verify if the live AdventureWorks database is online.
    """
    try:
        conn = get_connection()
        conn.close()
        return True, "Connected to AdventureWorks2019 on SQL Server"
    except Exception as e:
        return False, str(e)
