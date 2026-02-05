import boto3
import sys

dynamodb = boto3.client('dynamodb')

file = sys.argv[1]
city = sys.argv[2]

print(file)
#route_type,route_id,route_short_name,route_long_name,agency_id,route_desc,route_url,route_color,route_text_color
import csv
with open(file, newline='') as csvfile:
    spamreader = csv.DictReader(csvfile)
    for row in spamreader:
        dynamodb.put_item(TableName='routes', Item={
        'city':{'S':city},
        'id':{'S':row["route_type"] + "_" + row["route_id"]},
        'route_type':{'S':row["route_type"]},
        'route_id':{'N':row["route_id"]},
        'route_short_name':{'S':row["route_short_name"]},
        'route_long_name':{'S':row["route_long_name"]},
        'agency_id':{'S':row["agency_id"]},
        'route_desc':{'S':row["route_desc"]},
        'route_url':{'S':row["route_url"]},
        'route_color':{'S':row["route_color"]},
        'route_text_color':{'S':row["route_text_color"]},
    })