from psycopg2 import errors, sql


def createColumn(cursor, columns, table):
    for column in columns.split(","):
        column = column.strip()
        if not column:
            continue

        try:
            cursor.execute(
                sql.SQL("ALTER TABLE {} ADD {} TEXT NULL").format(
                    sql.Identifier(table),
                    sql.Identifier(column),
                )
            )
        except errors.DuplicateColumn:
            # Column already exists and does not need to be recreated.
            print(f"Warning: column already exists and is skipped: {table}.{column}")
