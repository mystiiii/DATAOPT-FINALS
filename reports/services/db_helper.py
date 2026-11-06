import logging
from django.db import connections
from django.db.utils import OperationalError, DatabaseError

logger = logging.getLogger(__name__)

def execute_query(sql, params=None, db_alias='adventureworks'):
    """
    Safely executes an SQL query on the specified database connection.
    Returns a list of dictionaries where keys are column names.
    """
    try:
        connection = connections[db_alias]
        with connection.cursor() as cursor:
            cursor.execute(sql, params or [])
            if cursor.description:
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            return []
    except (OperationalError, DatabaseError, Exception) as e:
        logger.warning(f"Database query on '{db_alias}' failed: {e}. Falling back to empty or mock data.")
        return None
