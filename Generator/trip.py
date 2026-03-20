import csv
import util.createColumnDoesNotExist

def insert(file, c):
    print(file)

    try:
        with open(file, newline="", encoding="utf8") as csvfile:
            line = csvfile.readline().strip()
            if not line:
                raise ValueError(f"Missing CSV header in {file}")

            util.createColumnDoesNotExist.createColumn(c, line, "trip")
            copy_columns = util.createColumnDoesNotExist.format_copy_columns(line)
            c.copy_expert("COPY trip (" + copy_columns + ") FROM STDIN (FORMAT CSV)", csvfile)
    except Exception as err:
        raise RuntimeError(f"Failed to import {file} into trip: {err}") from err