import boto3
import sys

dynamodb = boto3.client('dynamodb')

file = sys.argv[1]
city = sys.argv[2]

print(file)
#shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence,shape_dist_traveled
import csv
with open(file, newline='') as csvfile:
    spamreader = csv.DictReader(csvfile)
    for row in spamreader:
        dynamodb.put_item(TableName='shapes', Item={
        'city':{'S':city},
        'id':{'S':row["shape_id"] + "_" + row["shape_pt_sequence"]},
        'shape_id':{'S':row["shape_id"]},
        'shape_pt_lat':{'N':row["shape_pt_lat"]},
        'shape_pt_lon':{'N':row["shape_pt_lon"]},
        'shape_pt_sequence':{'N':row["shape_pt_sequence"]},
        'shape_dist_traveled':{'S':row["shape_dist_traveled"]},
        })