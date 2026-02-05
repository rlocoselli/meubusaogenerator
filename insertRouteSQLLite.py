import sys
import sqlite3

file = sys.argv[1]
db = sys.argv[2]

conn = sqlite3.connect(db)

c = conn.cursor()

print(file)
import csv

c.execute("delete from route")

try:
    c.execute("alter table route add favorite integer")
except Exception as err:
    print ("Column favorite already in place")

with open(file, newline='',encoding="utf8") as csvfile:
    spamreader = csv.DictReader(csvfile)
    
    for row in spamreader:

        if "route_desc" in row:
            sql = "INSERT INTO route VALUES ('" + row["route_type"] + "','" + row["route_id"] + "','"
            sql = sql + row["route_short_name"] + "','"
            sql = sql + row["route_long_name"].replace("'","''") + "','"
            if "agency_id" in row:            
                sql = sql + row["agency_id"] + "','"
            else:
                sql = sql + "','"           
            sql = sql + row["route_desc"].replace("'","''") + "','"
            sql = sql + row["route_url"] + "','"
            if "route_color" in row:
                sql = sql + row["route_color"] + "','"
            else:
                sql = sql + "','"
            if "route_text_color" in row:
                sql = sql + row["route_text_color"] + "',0)"
            else:
                sql = sql + "',0)"
        else:
            sql = "INSERT INTO route VALUES ('" + row["route_type"] + "','" + row["route_id"] + "','"
            sql = sql + row["route_short_name"] + "','"
            sql = sql + row["route_long_name"].replace("'","''") + "','"
            if "agency_id" in row:            
                sql = sql + row["agency_id"] + "','"
            else:
                sql = sql + "','"           
            sql = sql + row["route_short_name"].replace("'","''") + "','"
            sql = sql + row["route_short_name"] + "','"
            if "route_color" in row:
                sql = sql + row["route_color"] + "','"
            else:
                sql = sql + "','"
            if "route_text_color" in row:
                sql = sql + row["route_text_color"] + "',0)"
            else:
                sql = sql + "',0)"

        c.execute(sql)

conn.commit()
conn.close()

