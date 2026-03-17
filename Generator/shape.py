import csv
import util.createColumnDoesNotExist

def insert(file, c):
    print(file)

    c.execute("delete from shape")

    try:
        with open(file, newline="", encoding="utf8") as csvfile:
            line = csvfile.readline().strip()
            if not line:
                raise ValueError(f"Missing CSV header in {file}")

            util.createColumnDoesNotExist.createColumn(c, line, "shape")
            c.copy_expert("COPY shape (" + line + ") FROM STDIN (FORMAT CSV)", csvfile)
    except Exception as err:
        raise RuntimeError(f"Failed to import {file} into shape: {err}") from err