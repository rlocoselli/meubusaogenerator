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
    return ", ".join(f'"{column.replace("\"", "\"\"")}"' for column in parsed_columns)


def createColumn(cursor, columns, table):
    for column in parse_columns(columns):

        cursor.execute(
            sql.SQL("ALTER TABLE {} ADD COLUMN IF NOT EXISTS {} TEXT NULL").format(
                sql.Identifier(table),
                sql.Identifier(column),
            )
        )
