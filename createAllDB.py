import os
import re
from urllib.parse import urlparse
import ddl
from postgresConnection import getConnection
from zipfile import ZipFile
from zipfile import BadZipFile
import requests
from Generator import calendar_dates, calendar, fare, route, shape, stops, stopstimes, trip
from calculateDistanceStopsPostgres import GenerateTimes
from psycopg2 import errors, sql

DEFAULT_INSECURE_SSL_HOSTS = {"www.meubusao.com"}
PORTO_ALEGRE_DATABASE = "PortoAlegre_Brazil"


def _parse_database_filter_env(var_name):
    raw_value = os.environ.get(var_name, "")
    return {item.strip() for item in raw_value.split(",") if item.strip()}


def should_process_database(database_name, included_databases=None, excluded_databases=None):
    if included_databases and database_name not in included_databases:
        return False

    if excluded_databases and database_name in excluded_databases:
        return False

    return True


def _is_github_actions():
    return os.environ.get("GITHUB_ACTIONS", "").strip().lower() == "true"


def gha_notice(message):
    if _is_github_actions():
        print(f"::notice::{message}")
    else:
        print(message)

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


def _is_truthy_env_var(value):
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _is_insecure_ssl_allowed(url):
    # Global switch to allow insecure SSL for all hosts.
    if _is_truthy_env_var(os.environ.get("ALLOW_INSECURE_SSL_DOWNLOAD")):
        return True

    host = (urlparse(url).hostname or "").lower()
    if host in DEFAULT_INSECURE_SSL_HOSTS:
        return True

    host_allow_list = os.environ.get("ALLOW_INSECURE_SSL_HOSTS", "")
    if not host_allow_list.strip():
        return False

    allowed_hosts = {item.strip().lower() for item in host_allow_list.split(",") if item.strip()}
    return host in allowed_hosts


def download_and_unzip(url, destination, warning_handler):
    verify_ssl = True

    try:
        response = requests.get(url, timeout=60, verify=verify_ssl)
    except requests.exceptions.SSLError as err:
        if not _is_insecure_ssl_allowed(url):
            raise RuntimeError(
                "SSL certificate verification failed. "
                "Fix server certificate chain or set ALLOW_INSECURE_SSL_DOWNLOAD=true "
                "(or ALLOW_INSECURE_SSL_HOSTS=<host>) to force an insecure retry. "
                f"Known default insecure hosts: {', '.join(sorted(DEFAULT_INSECURE_SSL_HOSTS))}. "
                f"Original error: {err}"
            ) from err

        warning_handler(
            "SSL certificate verification failed, retrying insecurely for "
            f"{url}. This should be temporary and fixed at source."
        )
        verify_ssl = False
        requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined]
        response = requests.get(url, timeout=60, verify=verify_ssl)

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


# Databases whose GTFS calendar end_date should be extended to far-future
# because the feed is no longer actively maintained/updated.
_EXTEND_CALENDAR_DATABASES = {"Managua_Nicaragua"}


def fix_expired_calendar(cursor, database_name, warning_handler):
    """Set end_date to 20991231 in the calendar table for stale feeds."""
    try:
        cursor.execute("UPDATE calendar SET end_date = '20991231'")
        warning_handler(
            f"Calendar end_date extended to 20991231 for {database_name}"
        )
    except Exception as err:
        warning_handler(
            f"Failed to extend calendar end_date for {database_name}: {err}"
        )


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


def validate_and_clean_stop_times(database_name, cursor, log_handler):
    """Apply lightweight cleanup and consistency fixes on stopstime data."""
    # Normalize blank strings to NULL and trim surrounding spaces.
    cursor.execute(
        """
        UPDATE stopstime
        SET
            trip_id = NULLIF(BTRIM(trip_id), ''),
            stop_id = NULLIF(BTRIM(stop_id), ''),
            arrival_time = NULLIF(BTRIM(arrival_time), ''),
            departure_time = NULLIF(BTRIM(departure_time), '')
        """
    )

    cursor.execute(
        """
        UPDATE stopstime
        SET
            arrival_time = departure_time
        WHERE arrival_time IS NULL
          AND departure_time IS NOT NULL
        """
    )
    mirrored_arrivals = cursor.rowcount

    cursor.execute(
        """
        UPDATE stopstime
        SET
            departure_time = arrival_time
        WHERE departure_time IS NULL
          AND arrival_time IS NOT NULL
        """
    )
    mirrored_departures = cursor.rowcount

    cursor.execute(
        """
        DELETE FROM stopstime
        WHERE trip_id IS NULL
           OR stop_id IS NULL
           OR stop_sequence IS NULL
        """
    )
    removed_invalid_rows = cursor.rowcount

    cursor.execute(
        """
        WITH ranked AS (
            SELECT ctid,
                   ROW_NUMBER() OVER (
                       PARTITION BY trip_id, stop_sequence
                       ORDER BY ctid
                   ) AS rn
            FROM stopstime
        )
        DELETE FROM stopstime s
        USING ranked r
        WHERE s.ctid = r.ctid
          AND r.rn > 1
        """
    )
    removed_duplicates = cursor.rowcount

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM stopstime
        WHERE (
            arrival_time IS NOT NULL
            AND arrival_time !~ '^\\d+:\\d{2}:\\d{2}$'
        ) OR (
            departure_time IS NOT NULL
            AND departure_time !~ '^\\d+:\\d{2}:\\d{2}$'
        )
        """
    )
    invalid_time_rows = cursor.fetchone()[0]

    if invalid_time_rows > 0:
        log_handler(
            (
                f"Detected {invalid_time_rows} stopstime row(s) with non GTFS-like "
                "time format (expected H+:MM:SS)"
            ),
            level="WARNING",
        )

    if (
        mirrored_arrivals > 0
        or mirrored_departures > 0
        or removed_invalid_rows > 0
        or removed_duplicates > 0
    ):
        log_handler(
            (
                f"stopstime cleanup for {database_name}: mirrored_arrivals={mirrored_arrivals}, "
                f"mirrored_departures={mirrored_departures}, removed_invalid_rows={removed_invalid_rows}, "
                f"removed_duplicates={removed_duplicates}"
            ),
            level="INFO",
        )

    return {
        "mirrored_arrivals": mirrored_arrivals,
        "mirrored_departures": mirrored_departures,
        "removed_invalid_rows": removed_invalid_rows,
        "removed_duplicates": removed_duplicates,
        "invalid_time_rows": invalid_time_rows,
    }


def apply_post_import_rules(database_name, cursor, conn, log_handler):
    cleanup_stats = validate_and_clean_stop_times(database_name, cursor, log_handler)

    interpolation_stats = GenerateTimes(cursor, conn, None, None)
    updated_rows = interpolation_stats["updated_rows"]
    local_anchor_rows = interpolation_stats["local_anchor_rows"]
    global_fallback_rows = interpolation_stats["global_fallback_rows"]

    if database_name == PORTO_ALEGRE_DATABASE:
        log_handler(
            (
                f"Interpolated missing stop times for {database_name} "
                f"(updated={updated_rows}, local_anchor={local_anchor_rows}, "
                f"global_fallback={global_fallback_rows})"
            ),
            level="INFO",
        )
    elif updated_rows > 0:
        log_handler(
            (
                f"Applied Porto Alegre-like interpolation rule for {database_name} "
                f"(updated={updated_rows}, local_anchor={local_anchor_rows}, "
                f"global_fallback={global_fallback_rows})"
            ),
            level="INFO",
        )

    return {
        "cleanup": cleanup_stats,
        "interpolation": interpolation_stats,
    }


def _build_report_markdown(report_items):
    lines = [
        "## GTFS Validation Report",
        "",
        "| Database | Status | Warnings | Mirrored Arrivals | Mirrored Departures | Invalid Rows Removed | Duplicates Removed | Invalid Time Format Rows | Interpolated Total | Local Anchor | Global Fallback |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for item in report_items:
        cleanup = item.get("cleanup", {})
        interpolation = item.get("interpolation", {})
        status = "SUCCESS" if item.get("success") else "FAILED"

        lines.append(
            "| {database} | {status} | {warnings} | {mirrored_arrivals} | "
            "{mirrored_departures} | {removed_invalid_rows} | {removed_duplicates} | "
            "{invalid_time_rows} | {updated_rows} | {local_anchor_rows} | {global_fallback_rows} |".format(
                database=item.get("database", "unknown"),
                status=status,
                warnings=item.get("warning_count", 0),
                mirrored_arrivals=cleanup.get("mirrored_arrivals", 0),
                mirrored_departures=cleanup.get("mirrored_departures", 0),
                removed_invalid_rows=cleanup.get("removed_invalid_rows", 0),
                removed_duplicates=cleanup.get("removed_duplicates", 0),
                invalid_time_rows=cleanup.get("invalid_time_rows", 0),
                updated_rows=interpolation.get("updated_rows", 0),
                local_anchor_rows=interpolation.get("local_anchor_rows", 0),
                global_fallback_rows=interpolation.get("global_fallback_rows", 0),
            )
        )

    lines.append("")
    return "\n".join(lines)


def _build_progress_markdown(total, processed, succeeded, failed, current_database=None):
    if total <= 0:
        percent = 0
        filled = 0
    else:
        percent = int((processed / total) * 100)
        filled = int((processed / total) * 20)

    bar = "#" * filled + "-" * (20 - filled)

    lines = [
        "## GTFS Import Progress",
        "",
        f"- Processed: **{processed}/{total}** ({percent}%)",
        f"- Progress bar: [{bar}]",
        f"- Succeeded: **{succeeded}**",
        f"- Failed: **{failed}**",
    ]

    if current_database:
        lines.append(f"- Current database: **{current_database}**")

    lines.append("")
    return "\n".join(lines)


def publish_report_summary(report_items, total=0, processed=0, succeeded=0, failed=0, current_database=None):
    progress_markdown = _build_progress_markdown(
        total=total,
        processed=processed,
        succeeded=succeeded,
        failed=failed,
        current_database=current_database,
    )
    report_markdown = _build_report_markdown(report_items)
    summary_content = progress_markdown + report_markdown
    print(summary_content)

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "").strip()
    if not summary_path:
        return

    try:
        with open(summary_path, "w", encoding="utf8") as summary_file:
            summary_file.write(summary_content)
            summary_file.write("\n")
    except Exception as err:
        print(f"Warning: unable to write GitHub step summary: {err}")


def import_subdir(subdir, admin_conn):
    database_name = subdir.replace("./", "")
    url_file_path = os.path.join(subdir, "url.txt")
    report_item = {
        "database": database_name,
        "success": False,
        "warning_count": 0,
        "cleanup": {},
        "interpolation": {},
    }

    def log_handler(message, level="WARNING"):
        full_message = f"[{database_name}] {message}"
        print(full_message)
        safe_log_message(admin_conn, full_message, level=level)

    def warning_handler(message):
        log_handler(message, level="WARNING")

    with admin_conn.cursor() as admin_cursor:
        if not os.path.exists(url_file_path):
            message = f"url.txt not found in {subdir}"
            print(message)
            log_message(admin_cursor, message, level="ERROR")
            return report_item

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
        download_and_unzip(url, subdir, warning_handler)
        warning_count += insert_data_from_generator(subdir, db_cursor, warning_handler)

        if database_name in _EXTEND_CALENDAR_DATABASES:
            fix_expired_calendar(db_cursor, database_name, warning_handler)

        warning_count += create_indexes(db_cursor, warning_handler)
        post_import_stats = apply_post_import_rules(database_name, db_cursor, db_conn, log_handler)

        db_conn.commit()
        report_item["success"] = True
        report_item["warning_count"] = warning_count
        report_item["cleanup"] = post_import_stats.get("cleanup", {})
        report_item["interpolation"] = post_import_stats.get("interpolation", {})

        if warning_count > 0:
            success_message = (
                f"Import completed with warnings for {database_name} "
                f"({warning_count} warning(s))"
            )
        else:
            success_message = f"Import succeeded for {database_name}"

        print(success_message)
        safe_log_message(admin_conn, success_message, level="INFO")
        return report_item
    except Exception as err:
        if db_conn is not None:
            db_conn.rollback()

        error_message = f"Import failed for {database_name}: {err}"
        print(error_message)
        safe_log_message(admin_conn, error_message, level="ERROR")
        return report_item
    finally:
        if db_cursor is not None:
            db_cursor.close()
        if db_conn is not None:
            db_conn.close()


def main():
    subdirs = [x[0] for x in os.walk(".")]
    included_databases = _parse_database_filter_env("INCLUDED_DATABASES")
    excluded_databases = _parse_database_filter_env("EXCLUDED_DATABASES")
    databases_to_process = []
    for subdir in subdirs:
        if "_" not in subdir or "__pycache__" in subdir:
            continue

        database_name = subdir.replace("./", "")
        if not should_process_database(
            database_name,
            included_databases=included_databases,
            excluded_databases=excluded_databases,
        ):
            continue

        databases_to_process.append(subdir)

    total = len(databases_to_process)
    admin_conn = getConnection("postgres")

    try:
        with admin_conn.cursor() as cursor:
            create_log_table(cursor)

        processed = 0
        succeeded = 0
        failed = 0
        report_items = []

        gha_notice(f"GTFS import started for {total} database(s)")

        if total > 0:
            publish_report_summary(
                report_items,
                total=total,
                processed=processed,
                succeeded=succeeded,
                failed=failed,
            )

        for subdir in databases_to_process:
            database_name = subdir.replace("./", "")
            gha_notice(f"Starting import for {database_name}")
            print(f"Starting import for {subdir}")
            report_item = import_subdir(subdir, admin_conn)
            report_items.append(report_item)
            processed += 1
            if report_item.get("success"):
                succeeded += 1
                gha_notice(f"Completed import for {database_name} ({processed}/{total})")
            else:
                failed += 1
                gha_notice(f"Failed import for {database_name} ({processed}/{total})")

            publish_report_summary(
                report_items,
                total=total,
                processed=processed,
                succeeded=succeeded,
                failed=failed,
                current_database=database_name,
            )

        print(f"Import finished. Success: {succeeded}/{total}")
        gha_notice(f"GTFS import finished. Success: {succeeded}/{total}, Failed: {failed}")
    finally:
        admin_conn.close()

if __name__ == "__main__":
    main()

