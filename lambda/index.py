"""Lambda function to fetch and store Japanese holidays."""
import os
from datetime import datetime, timedelta

import boto3
import jpholiday
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError

# Initialize AWS Powertools Logger
logger = Logger(service=os.getenv("POWERTOOLS_SERVICE_NAME", "jpholiday"))

# Initialize DynamoDB resource
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])


def handler(event: dict, context: LambdaContext) -> dict:
    """Lambda handler function to process Japanese holidays.

    Args:
        event: Lambda event object
        context: Lambda context object

    Returns:
        dict: Response with status code and body
    """
    # Set correlation ID for request tracing
    logger.set_correlation_id(context.aws_request_id)

    logger.info("Starting holiday data update process", extra={"event": event})

    try:
        current_date = datetime.now()
        end_date = current_date + timedelta(days=365)

        logger.info(
            "Fetching holidays",
            extra={
                "start_date": current_date.date().isoformat(),
                "end_date": end_date.date().isoformat(),
            },
        )

        holidays = jpholiday.between(current_date, end_date)
        holiday_count = len(holidays)

        logger.info(f"Found {holiday_count} holidays to process")

        # Write holidays to DynamoDB
        with table.batch_writer() as batch:
            for holiday_date, holiday_name in holidays:
                item = {"date": holiday_date.strftime("%Y-%m-%d"), "name": holiday_name}
                batch.put_item(Item=item)
                logger.debug(f"Writing holiday: {holiday_name} on {holiday_date}")

        logger.info(
            "Successfully updated holidays",
            extra={
                "holiday_count": holiday_count,
                "start_date": current_date.date().isoformat(),
                "end_date": end_date.date().isoformat(),
            },
        )

        return {
            "statusCode": 200,
            "body": f"Successfully updated {holiday_count} holidays from {current_date.date()} to {end_date.date()}",
        }

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        logger.error(
            "DynamoDB client error",
            extra={"error_code": error_code, "error_message": error_message},
            exc_info=True,
        )
        return {
            "statusCode": 500,
            "body": f"DynamoDB error: {error_code} - {error_message}",
        }

    except Exception as e:
        logger.error("Unexpected error occurred", exc_info=True)
        return {
            "statusCode": 500,
            "body": f"Internal server error: {str(e)}",
        }
