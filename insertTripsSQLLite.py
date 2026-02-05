import sys
import sqlite3

file = sys.argv[1]
db = sys.argv[2]

conn = sqlite3.connect(db)

c = conn.cursor()

c.execute("delete from trip")

print(file)
import csv
with open(file, newline='',encoding="utf8") as csvfile:
    spamreader = csv.DictReader(csvfile)
    for row in spamreader:
        
        sql = "INSERT INTO trip VALUES ('" + row["trip_id"] + "','" + row["route_id"] + "','"
        sql = sql + row["trip_headsign"].replace("'","") + "','"
        sql = sql + row["service_id"] + "','"
        sql = sql + row["shape_id"] + "','"
        if "block_id" in row:
            sql = sql + row["block_id"] + "','"
        else:
            sql = sql + "','"
        if "wheelchair_accessible" in row:
            sql = sql + row["wheelchair_accessible"] + "','"
        else:
            sql = sql + "','"

        if "bikes_allowed" in row:
            sql = sql + row["bikes_allowed"] + "','"
        else:
            sql = sql + "','"
            
        if "direction_id" in row:
            sql = sql + row["direction_id"] + "')"
        else:
            sql += "')"

        c.execute(sql)

conn.commit()
conn.close()