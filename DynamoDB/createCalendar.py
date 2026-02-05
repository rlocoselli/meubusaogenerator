import boto3

# Get the service resource.
dynamodb = boto3.resource('dynamodb')

# Create the DynamoDB table.
table = dynamodb.create_table(
    TableName='calendar',
    KeySchema=[
        {
            'AttributeName': 'city',
            'KeyType': 'HASH'
        },
        {
            'AttributeName': 'service_id',
            'KeyType': 'RANGE'
        }
    ],
    AttributeDefinitions=[
        {
            'AttributeName': 'city',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'service_id',
            'AttributeType': 'S'
        },
    ],
    ProvisionedThroughput={
        'ReadCapacityUnits': 5,
        'WriteCapacityUnits': 5
    }
)

# Wait until the table exists.
table.meta.client.get_waiter('table_exists').wait(TableName='fare_attributes')

# Print out some data about the table.
print(table.item_count)