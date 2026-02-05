import sys
import sqlite3

file = sys.argv[1]
db = sys.argv[2]

conn = sqlite3.connect(db)

c = conn.cursor()

c.execute("delete from fare_attributes")

print(file)
import csv
with open(file, newline='',encoding="utf8") as csvfile:
    spamreader = csv.DictReader(csvfile)
    for row in spamreader:
        
        sql = "INSERT INTO fare_attributes VALUES ('" + row["fare_id"] + "','" + row["price"] + "','"
        sql = sql + row["currency_type"] + "','"
        sql = sql + row["payment_method"] + "','"
        sql = sql + row["transfers"] + "','"
        sql = sql + row["transfer_duration"] + "')"
        
        print (sql)

        c.execute(sql)

conn.commit()
conn.close()