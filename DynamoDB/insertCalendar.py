import boto3
import sys

dynamodb = boto3.client('dynamodb')

file = sys.argv[1]
city = sys.argv[2]

print(file)
#service_id,start_date,end_date,monday,tuesday,wednesday,thursday,friday,saturday,sunday
import csv
with open(file, newline='') as csvfile:
    spamreader = csv.DictReader(csvfile)
    for row in spamreader:
        dynamodb.put_item(TableName='calendar', Item={
        'city':{'S':city},
        'service_id':{'S':row["service_id"]},
        'start_date':{'S':row["start_date"]},
        'end_date':{'S':row["end_date"]},
        'monday':{'S':row["monday"]},
        'tuesday':{'S':row["tuesday"]},
        'wednesday':{'S':row["wednesday"]},
        'thursday':{'S':row["thursday"]},
        'friday':{'S':row["friday"]},
        'saturday':{'S':row["saturday"]},
        'sunday':{'S':row["sunday"]},
        })