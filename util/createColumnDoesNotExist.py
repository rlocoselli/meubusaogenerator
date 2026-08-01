import csv
from psycopg2 import sql


def parse_columns(columns):
    if isinstance(columns, str):
        parsed_columns = next(csv.reader([columns]))
    else:
        parsed_columns = list(columns)

    cleaned_columns = []
    for column in parsed_columns:
        normalized = column.strip().lstrip("\ufeff")
        if normalized:
            cleaned_columns.append(normalized)

    return cleaned_columns


def format_copy_columns(columns):
    parsed_columns = parse_columns(columns)
    return ", ".join('"{}"'.format(column.replace('"', '""')) for column in parsed_columns)


def createColumn(cursor, columns, table):
    parsed_columns = parse_columns(columns)
    if not parsed_columns:
        return

    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = %s
        """,
        (table,),
    )
    existing_columns = {row[0] for row in cursor.fetchall()}
    missing_columns = [column for column in parsed_columns if column not in existing_columns]

    if not missing_columns:
        return

    add_column_clauses = [
        sql.SQL("ADD COLUMN IF NOT EXISTS {} TEXT NULL").format(sql.Identifier(column))
        for column in missing_columns
    ]

    cursor.execute(
        sql.SQL("ALTER TABLE {} ").format(sql.Identifier(table))
        + sql.SQL(", ").join(add_column_clauses)
    )
