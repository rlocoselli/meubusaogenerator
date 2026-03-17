import csv
import util.createColumnDoesNotExist
from psycopg2 import errors

def insert(file, c):
    print(file)
    c.execute("delete from route")

    try:
        c.execute("alter table route add favorite integer")
    except errors.DuplicateColumn:
        pass

    try:
        with open(file, newline="", encoding="utf8") as csvfile:
            line = csvfile.readline().strip()
            if not line:
                raise ValueError(f"Missing CSV header in {file}")

            util.createColumnDoesNotExist.createColumn(c, line, "route")
            c.copy_expert("COPY route (" + line + ") FROM STDIN (FORMAT CSV)", csvfile)
    except Exception as err:
        raise RuntimeError(f"Failed to import {file} into route: {err}") from err