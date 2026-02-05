import sys
import sqlite3

file = sys.argv[1]
db = sys.argv[2]

conn = sqlite3.connect(db)

c = conn.cursor()

c.execute("delete from stops")

print(file)
import csv
with open(file, newline='',encoding="utf8") as csvfile:
    spamreader = csv.DictReader(csvfile)
    for row in spamreader:

        sql = "INSERT INTO stops VALUES ('" + row["stop_name"].replace("'","") + "','" + row["stop_id"] + "','"
        sql = sql + row["stop_lat"] + "','"
        sql = sql + row["stop_lon"] + "','"
        if "parent_station" in row:
            sql = sql + row["parent_station"] + "','"
        else:
            sql = sql + "','"
        if "location_type" in row:
            sql = sql + row["location_type"] + "')"
        else:
            sql = sql + "')"

        c.execute(sql)

conn.commit()
conn.close()