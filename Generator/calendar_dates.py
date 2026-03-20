import csv
import util.createColumnDoesNotExist

def insert(file, c):
    print(file)

    c.execute("delete from calendar_dates")

    try:
        with open(file, newline="", encoding="utf8") as csvfile:
            line = csvfile.readline().strip()
            if not line:
                raise ValueError(f"Missing CSV header in {file}")

            util.createColumnDoesNotExist.createColumn(c, line, "calendar_dates")
            copy_columns = util.createColumnDoesNotExist.format_copy_columns(line)
            c.copy_expert("COPY calendar_dates (" + copy_columns + ") FROM STDIN (FORMAT CSV)", csvfile)

        c.execute("UPDATE CALENDAR_DATES SET DATET = DATE WHERE DATET IS NULL")
    except Exception as err:
        raise RuntimeError(f"Failed to import {file} into calendar_dates: {err}") from err