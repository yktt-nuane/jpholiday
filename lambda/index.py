# lambda/index.py
import os
import boto3
import jpholiday
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def handler(event, context):
    current_date = datetime.now()
    end_date = current_date + timedelta(days=365)

    holidays = jpholiday.between(current_date, end_date)

    with table.batch_writer() as batch:
        for holiday_date, holiday_name in holidays:
            batch.put_item(
                Item={
                    'date': holiday_date.strftime('%Y-%m-%d'),
                    'name': holiday_name
                }
            )

    return {
        'statusCode': 200,
        'body': f'Successfully updated holidays from {current_date.date()} to {end_date.date()}'
    }
