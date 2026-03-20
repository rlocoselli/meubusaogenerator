import csv
import util.createColumnDoesNotExist

def insert(file, c):
    print(file)
    c.execute("delete from route")
    c.execute("ALTER TABLE route ADD COLUMN IF NOT EXISTS favorite integer")

    try:
        with open(file, newline="", encoding="utf8") as csvfile:
            line = csvfile.readline().strip()
            if not line:
                raise ValueError(f"Missing CSV header in {file}")

            util.createColumnDoesNotExist.createColumn(c, line, "route")
            copy_columns = util.createColumnDoesNotExist.format_copy_columns(line)
            c.copy_expert("COPY route (" + copy_columns + ") FROM STDIN (FORMAT CSV)", csvfile)
    except Exception as err:
        raise RuntimeError(f"Failed to import {file} into route: {err}") from err