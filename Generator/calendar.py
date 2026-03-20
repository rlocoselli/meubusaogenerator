import csv
import util.createColumnDoesNotExist

def insert(file, c):
    print(file)

    c.execute("delete from calendar")

    try:
        with open(file, newline="", encoding="utf8") as csvfile:
            line = csvfile.readline().strip()
            if not line:
                raise ValueError(f"Missing CSV header in {file}")

            util.createColumnDoesNotExist.createColumn(c, line, "calendar")
            copy_columns = util.createColumnDoesNotExist.format_copy_columns(line)
            c.copy_expert("COPY calendar (" + copy_columns + ") FROM STDIN (FORMAT CSV)", csvfile)
    except Exception as err:
        raise RuntimeError(f"Failed to import {file} into calendar: {err}") from err