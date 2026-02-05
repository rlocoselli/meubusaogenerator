import sys
import sqlite3

file = sys.argv[1]
db = sys.argv[2]

conn = sqlite3.connect(db)

c = conn.cursor()

c.execute("delete from calendar_dates")

print(file)
import csv
with open(file, newline='') as csvfile:
    spamreader = csv.DictReader(csvfile)
    for row in spamreader:

        sql = "INSERT INTO calendar_dates VALUES ('" + row["service_id"] + "','" + row["date"] + "','"
        sql = sql + row["exception_type"] + "')"
        
        c.execute(sql)

conn.commit()
conn.close()