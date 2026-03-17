import os
import re
import ddl
from postgresConnection import getConnection
from zipfile import ZipFile
from zipfile import BadZipFile
import requests
from Generator import calendar_dates, calendar, fare, route, shape, stops, stopstimes, trip
from psycopg2 import errors, sql

def create_log_table(cursor):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS log (
        id SERIAL PRIMARY KEY,
        level TEXT NOT NULL DEFAULT 'INFO',
        message TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    cursor.execute(create_table_query)
    cursor.execute("ALTER TABLE log ADD COLUMN IF NOT EXISTS level TEXT NOT NULL DEFAULT 'INFO'")

def log_message(cursor, message, level="INFO"):
    insert_query = """
    INSERT INTO log (level, message) VALUES (%s, %s)
    """
    cursor.execute(insert_query, (level, message))


def safe_log_message(admin_conn, message, level="INFO"):
    try:
        with admin_conn.cursor() as admin_cursor:
            log_message(admin_cursor, message, level)
    except Exception as err:
        print(f"Warning: unable to write to log table: {err}")
        print(f"Original {level} log message: {message}")


def download_and_unzip(url, destination):
    response = requests.get(url, timeout=60)
    response.raise_for_status()

    zip_filename = os.path.join(destination, "data.zip")
    with open(zip_filename, "wb") as f:
        f.write(response.content)

    try:
        with ZipFile(zip_filename, "r") as zip_ref:
            zip_ref.extractall(destination)
    except BadZipFile as err:
        raise RuntimeError(f"Downloaded file is not a valid zip from URL: {url}") from err
    finally:
        if os.path.exists(zip_filename):
            os.remove(zip_filename)


def read_feed_url(url_file_path):
    with open(url_file_path, "r", encoding="utf8") as url_file:
        url = url_file.read().strip()

    if not url:
        raise ValueError(f"URL file is empty: {url_file_path}")

    return url


def insert_data_from_generator(subdir, cursor, warning_handler):
    import_steps = [
        ("calendar_dates.txt", calendar_dates.insert, False),
        ("calendar.txt", calendar.insert, False),
        ("fare_attributes.txt", fare.insert, False),
        ("routes.txt", route.insert, True),
        ("shapes.txt", shape.insert, False),
        ("stops.txt", stops.insert, True),
        ("stop_times.txt", stopstimes.insert, True),
        ("trips.txt", trip.insert, True),
    ]

    warning_count = 0

    for index, (filename, loader, required) in enumerate(import_steps, start=1):
        file_path = os.path.join(subdir, filename)
        if not os.path.exists(file_path):
            if required:
                warning_handler(f"Required file missing for import: {file_path}")
                warning_count += 1
                continue

            warning_handler(f"Optional file missing, skipping {file_path}")
            warning_count += 1
            continue

        savepoint_name = f"sp_import_{index}"
        cursor.execute(sql.SQL("SAVEPOINT {}").format(sql.Identifier(savepoint_name)))

        try:
            loader(file_path, cursor)
        except Exception as err:
            cursor.execute(
                sql.SQL("ROLLBACK TO SAVEPOINT {}").format(sql.Identifier(savepoint_name))
            )
            warning_handler(f"Failed importing {file_path}: {err}")
            warning_count += 1
        finally:
            cursor.execute(
                sql.SQL("RELEASE SAVEPOINT {}").format(sql.Identifier(savepoint_name))
            )

    return warning_count


def create_database_if_needed(admin_cursor, database_name):
    try:
        admin_cursor.execute(
            sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name))
        )
        print(f"Database created: {database_name}")
    except errors.DuplicateDatabase:
        print(f"Database already exists: {database_name}")


def drop_and_create_tables(cursor):
    for table in ddl.table_names:
        cursor.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(table)))

    for table in ddl.tables:
        cursor.execute(table)


def create_indexes(cursor, warning_handler):
    warning_count = 0

    for index_pos, index in enumerate(ddl.indexes, start=1):
        index_sql = index
        if "if not exists" not in index.lower() and index.lower().startswith("create index"):
            index_sql = re.sub(
                r"^create\s+index\s+",
                "CREATE INDEX IF NOT EXISTS ",
                index,
                count=1,
                flags=re.IGNORECASE,
            )

        savepoint_name = f"sp_index_{index_pos}"
        cursor.execute(sql.SQL("SAVEPOINT {}").format(sql.Identifier(savepoint_name)))
        try:
            cursor.execute(index_sql)
        except Exception as err:
            cursor.execute(
                sql.SQL("ROLLBACK TO SAVEPOINT {}").format(sql.Identifier(savepoint_name))
            )
            warning_handler(f"Index creation failed ({index_sql}): {err}")
            warning_count += 1
        finally:
            cursor.execute(
                sql.SQL("RELEASE SAVEPOINT {}").format(sql.Identifier(savepoint_name))
            )

    return warning_count


def import_subdir(subdir, admin_conn):
    database_name = subdir.replace("./", "")
    url_file_path = os.path.join(subdir, "url.txt")

    def warning_handler(message):
        full_message = f"[{database_name}] {message}"
        print(full_message)
        safe_log_message(admin_conn, full_message, level="WARNING")

    with admin_conn.cursor() as admin_cursor:
        if not os.path.exists(url_file_path):
            message = f"url.txt not found in {subdir}"
            print(message)
            log_message(admin_cursor, message, level="ERROR")
            return False

        create_database_if_needed(admin_cursor, database_name)

    db_conn = None
    db_cursor = None
    try:
        db_conn = getConnection(database_name)
        db_conn.autocommit = False
        db_cursor = db_conn.cursor()
        warning_count = 0

        drop_and_create_tables(db_cursor)

        url = read_feed_url(url_file_path)
        download_and_unzip(url, subdir)
        warning_count += insert_data_from_generator(subdir, db_cursor, warning_handler)
        warning_count += create_indexes(db_cursor, warning_handler)

        db_conn.commit()
        if warning_count > 0:
            success_message = (
                f"Import completed with warnings for {database_name} "
                f"({warning_count} warning(s))"
            )
        else:
            success_message = f"Import succeeded for {database_name}"

        print(success_message)
        safe_log_message(admin_conn, success_message, level="INFO")
        return True
    except Exception as err:
        if db_conn is not None:
            db_conn.rollback()

        error_message = f"Import failed for {database_name}: {err}"
        print(error_message)
        safe_log_message(admin_conn, error_message, level="ERROR")
        return False
    finally:
        if db_cursor is not None:
            db_cursor.close()
        if db_conn is not None:
            db_conn.close()


def main():
    subdirs = [x[0] for x in os.walk(".")]
    admin_conn = getConnection("postgres")

    try:
        with admin_conn.cursor() as cursor:
            create_log_table(cursor)

        total = 0
        succeeded = 0

        for subdir in subdirs:
            if "_" not in subdir or "__pycache__" in subdir:
                continue

            total += 1
            print(f"Starting import for {subdir}")
            if import_subdir(subdir, admin_conn):
                succeeded += 1

        print(f"Import finished. Success: {succeeded}/{total}")
    finally:
        admin_conn.close()

if __name__ == "__main__":
    main()

