import boto3
import sys

dynamodb = boto3.client('dynamodb')

file = sys.argv[1]
city = sys.argv[2]

print(file)

import csv

i = 0

with open(file, newline='') as csvfile:
    spamreader = csv.DictReader(csvfile)
    for row in spamreader:
        i+=1
        print(i)
        dynamodb.put_item(TableName='stopstime', Item={
        'city':{'S':city},
        'id':{'S':row["trip_id"] + '_' + row["stop_sequence"] + "_" + row["stop_id"] + "_" + row["arrival_time"] + "_" +row["departure_time"]},
        'trip_id':{'N':row["trip_id"]},
        'arrival_time':{'S':row["arrival_time"]},
        'departure_time':{'S':row["departure_time"]},
        'stop_id':{'S': row["stop_id"]},
        'stop_sequence':{'N':row["stop_sequence"]},
        'stop_headsign':{'S':row["stop_headsign"]},
        'pickup_type':{'S':row["pickup_type"]},
        'drop_off_type':{'S':row["drop_off_type"]},
        'shape_dist_traveled':{'S':row["shape_dist_traveled"]},
        'timepoint':{'S':row["timepoint"]},
        })
        