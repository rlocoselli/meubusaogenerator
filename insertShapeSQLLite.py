import sys
import sqlite3

file = sys.argv[1]
db = sys.argv[2]

conn = sqlite3.connect(db)

c = conn.cursor()

print(file)
import csv
with open(file, newline='') as csvfile:
    spamreader = csv.DictReader(csvfile)
    for row in spamreader:
        
        sql = "INSERT INTO shape VALUES ('" + row["shape_id"] + "','" + row["shape_pt_lat"].replace(',','.') + "','"
        sql = sql + row["shape_pt_lon"].replace(',','.') + "','"
        sql = sql + row["shape_pt_sequence"] + "','"
        if "shape_dist_traveled" in row:
            sql = sql + row["shape_dist_traveled"] + "')"
        else:
            sql = sql + "')"

        
        c.execute(sql)

conn.commit()
conn.close()