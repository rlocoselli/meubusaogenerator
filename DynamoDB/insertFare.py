import boto3
import sys

dynamodb = boto3.client('dynamodb')

file = sys.argv[1]
city = sys.argv[2]

print(file)
#fare_id,price,currency_type,payment_method,transfers,transfer_duration
import csv
with open(file, newline='') as csvfile:
    spamreader = csv.DictReader(csvfile)
    for row in spamreader:
        dynamodb.put_item(TableName='fare_attributes', Item={
        'city':{'S':city},
        'fare_id':{'N':row["fare_id"]},
        'price':{'N':row["price"]},
        'currency_type':{'S':row["currency_type"]},
        'payment_method':{'S':row["payment_method"]},
        'transfers':{'S':row["transfers"]},
        'transfer_duration':{'S':row["transfer_duration"]},
        })