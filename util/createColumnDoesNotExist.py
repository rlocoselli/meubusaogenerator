from psycopg2 import sql


def createColumn(cursor, columns, table):
    for column in columns.split(","):
        column = column.strip()
        if not column:
            continue

        cursor.execute(
            sql.SQL("ALTER TABLE {} ADD COLUMN IF NOT EXISTS {} TEXT NULL").format(
                sql.Identifier(table),
                sql.Identifier(column),
            )
        )
