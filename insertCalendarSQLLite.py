import sys
import sqlite3

file = sys.argv[1]
db = sys.argv[2]

conn = sqlite3.connect(db)

c = conn.cursor()

c.execute("delete from calendar")

print(file)
import csv
with open(file, newline='') as csvfile:
    spamreader = csv.DictReader(csvfile)
    for row in spamreader:

        sql = "INSERT INTO calendar VALUES ('" + row["service_id"] + "','" + row["start_date"] + "','"
        sql = sql + row["end_date"] + "','"
        sql = sql + row["monday"] + "','"
        sql = sql + row["tuesday"] + "','"
        sql = sql + row["wednesday"] + "','"
        sql = sql + row["thursday"] + "','"
        sql = sql + row["friday"] + "','"
        sql = sql + row["saturday"] + "','"
        sql = sql + row["sunday"] + "')"
        
        c.execute(sql)

conn.commit()
conn.close()