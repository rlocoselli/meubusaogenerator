import boto3
import sys

dynamodb = boto3.client('dynamodb')

file = sys.argv[1]
city = sys.argv[2]

print(file)
#fare_id,route_id,origin_id,destination_id,contains_id
import csv
with open(file, newline='') as csvfile:
    spamreader = csv.DictReader(csvfile)
    for row in spamreader:
        dynamodb.put_item(TableName='fare_rules', Item={
        'city':{'S':city},
        'fare_rules_id':{'S':row["fare_id"] + "_" + row["route_id"]},
        'fare_id':{'N':row["fare_id"]},
        'route_id':{'N':row["route_id"]},
        'origin_id':{'S':row["origin_id"]},
        'destination_id':{'S':row["destination_id"]},
        'contains_id':{'S':row["contains_id"]},
        })