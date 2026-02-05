import boto3
import sys

dynamodb = boto3.resource('dynamodb')

file = sys.argv[1]
city = sys.argv[2]

print(file)
#route_id,trip_id,trip_headsign,service_id,shape_id,block_id,wheelchair_accessible,bikes_allowed,direction_id
import csv
with open(file, newline='') as csvfile:
    spamreader = csv.DictReader(csvfile)
    for row in spamreader:
        dynamodb.put_item(TableName='trips', Item={
        'city':{'S':city},
        'id':{'S':row["route_id"] + "_" + row["trip_id"]},
        'trip_id':{'S':row["trip_id"]},
        'route_id':{'N':row["route_id"]},
        'trip_headsign':{'S':row["trip_headsign"]},
        'service_id':{'S':row["service_id"]},
        'shape_id':{'S':row["shape_id"]},
        'block_id':{'S':row["block_id"]},
        'wheelchair_accessible':{'S':row["wheelchair_accessible"]},
        'bikes_allowed':{'S':row["bikes_allowed"]},
        'direction_id':{'S':row["direction_id"]},
    })