"""Japanese Holiday Calendar CDK Stack definition."""

import os

from aws_cdk import Duration, RemovalPolicy, Stack
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_lambda as _lambda
from constructs import Construct
from dotenv import load_dotenv

load_dotenv()


class JpHolidayStack(Stack):
    """Japanese Holiday Calendar CDK Stack."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        """Initialize the Japanese Holiday Calendar stack.

        Args:
            scope: The scope in which to define this construct
            construct_id: The scoped construct ID
            **kwargs: Additional keyword arguments

        Raises:
            ValueError: If required environment variables are not set
        """
        super().__init__(scope, construct_id, **kwargs)

        # Get environment variables with proper type checking
        table_name = os.getenv("DYNAMODB_TABLE_NAME")
        if not table_name:
            raise ValueError("DYNAMODB_TABLE_NAME environment variable is required")

        lambda_memory_str = os.getenv("LAMBDA_MEMORY_SIZE")
        if not lambda_memory_str:
            raise ValueError("LAMBDA_MEMORY_SIZE environment variable is required")
        lambda_memory = int(lambda_memory_str)

        lambda_timeout_str = os.getenv("LAMBDA_TIMEOUT")
        if not lambda_timeout_str:
            raise ValueError("LAMBDA_TIMEOUT environment variable is required")
        lambda_timeout = int(lambda_timeout_str)

        stage = os.getenv("STAGE")
        if not stage:
            raise ValueError("STAGE environment variable is required")

        jpholiday_layer_arn = os.getenv("JPHOLIDAY_LAYER_ARN")
        if not jpholiday_layer_arn:
            raise ValueError("JPHOLIDAY_LAYER_ARN environment variable is required")

        # DynamoDB table
        holiday_table = dynamodb.Table(
            self,
            "HolidaysTable",
            table_name=table_name,
            partition_key=dynamodb.Attribute(name="date", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="name", type=dynamodb.AttributeType.STRING),
            removal_policy=RemovalPolicy.DESTROY if stage == "dev" else RemovalPolicy.RETAIN,
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        # Lambda Layer
        jpholiday_layer = _lambda.LayerVersion.from_layer_version_arn(
            self, "JpHolidayLayer", layer_version_arn=jpholiday_layer_arn
        )

        # Lambda function
        holiday_function = _lambda.Function(
            self,
            "JpHolidayFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(lambda_timeout),
            memory_size=lambda_memory,
            layers=[jpholiday_layer],
            environment={"TABLE_NAME": holiday_table.table_name, "STAGE": stage},
        )

        # Grant permissions
        holiday_table.grant_write_data(holiday_function)

        # CloudWatch Events Rule (EventBridge)
        events.Rule(
            self,
            "MonthlyRule",
            schedule=events.Schedule.cron(minute="0", hour="0", day="1", month="*", year="*"),
            targets=[targets.LambdaFunction(holiday_function)],
        )
