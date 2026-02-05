import sys
import sqlite3

file = sys.argv[1]
db = sys.argv[2]

conn = sqlite3.connect(db)

c = conn.cursor()

c.execute("delete from stopstime")

print(file)
import csv
with open(file, newline='',encoding="utf8") as csvfile:
    spamreader = csv.DictReader(csvfile)
    for row in spamreader:

        sql = "INSERT INTO stopstime VALUES ('" + row["trip_id"] + "','" + row["arrival_time"] + "','"
        sql = sql + row["departure_time"] + "','"
        sql = sql + row["stop_id"] + "','"
        sql = sql + row["stop_sequence"] + "','"
        
        if "stop_headsign" in row:
            sql = sql + row["stop_headsign"].replace("'","''") + "','"
        else:
            sql = sql + "','"

        if "pickup_type" in row:
            sql = sql + row["pickup_type"].replace("'","''") + "','"
        else:
            sql = sql + "','"

        if "drop_off_type" in row:
            sql = sql + row["drop_off_type"] + "','"
        else:
            sql = sql + "','"

        if "shape_dist_traveled" in row:
            sql = sql + row["shape_dist_traveled"] + "','"
        else:
            sql = sql + "','"

        if "timepoint" in row:
            sql = sql + row["timepoint"] + "')"
        else:
            sql = sql + "')"
        
        c.execute(sql)

conn.commit()
conn.close()