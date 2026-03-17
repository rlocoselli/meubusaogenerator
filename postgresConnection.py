import psycopg2
import os


def _get_connection_settings(database):
    required_vars = ["SERVER", "USER", "MOT"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        missing_list = ", ".join(missing_vars)
        raise RuntimeError(f"Missing required PostgreSQL environment variables: {missing_list}")

    return {
        "host": os.environ["SERVER"],
        "database": database,
        "user": os.environ["USER"],
        "password": os.environ["MOT"],
    }


def getConnectionCursor(database):
    conn = getConnection(database)
    conn.autocommit = True
    return conn.cursor()

def getConnection(database):
    settings = _get_connection_settings(database)
    try:
        conn = psycopg2.connect(**settings)
    except psycopg2.Error as err:
        raise RuntimeError(
            f"Unable to connect to PostgreSQL database '{database}' on host '{settings['host']}': {err}"
        ) from err

    conn.set_client_encoding("UTF8")
    conn.autocommit = True
    return conn