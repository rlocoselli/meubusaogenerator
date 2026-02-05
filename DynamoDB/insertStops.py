import boto3
import sys

dynamodb = boto3.client('dynamodb')

file = sys.argv[1]
city = sys.argv[2]

print(file)

import csv
with open(file, newline='') as csvfile:
    spamreader = csv.DictReader(csvfile)
    for row in spamreader:
        dynamodb.put_item(TableName='stops', Item={
        'city':{'S':city},
        'id':{'S':row["stop_lat"] + "_" + row["stop_lon"] + "_" + row["stop_name"]},
        'stop_name':{'S':row["stop_name"]},
        'stop_id':{'S':row["stop_id"]},
        'stop_lat':{'N':row["stop_lat"]},
        'stop_lon':{'N':row["stop_lon"]},
        'parent_station':{'S': "No Station" if row["parent_station"] == "" else row["parent_station"]},
        'location_type':{'S':row["location_type"]},})