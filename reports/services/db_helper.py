import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class DatabaseConnectionError(Exception):
    """Raised when live SQL Server AdventureWorks connection or query fails."""
    pass

def get_connection():
    """
    Connects to the Microsoft SQL Server AdventureWorks database using pymssql.
    """
    import pymssql
    host = os.getenv('DB_HOST', 'localhost')
    port = int(os.getenv('DB_PORT', 1434))
    user = os.getenv('DB_USER', 'sa')
    password = os.getenv('DB_PASSWORD', 'Password123')
    database = os.getenv('DB_NAME', 'AdventureWorks2019')

    try:
        return pymssql.connect(
            server=host,
            port=port,
            user=user,
            password=password,
            database=database,
            as_dict=True,
            timeout=3,
            login_timeout=3
        )
    except Exception as e:
        logger.error(f"Failed connecting to SQL Server at {host}:{port} ({database}): {e}")
        raise DatabaseConnectionError(f"Cannot connect to SQL Server database '{database}' on {host}:{port}. Error: {e}")

def execute_query(sql, params=None):
    """
    Executes raw SQL query on live AdventureWorks2019 database.
    Strictly returns database results. Never falls back to mock data.
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()
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
