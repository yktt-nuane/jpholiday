# stacks/jpholiday_stack.py
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as targets,
    Duration,
    RemovalPolicy,
)
from constructs import Construct
from dotenv import load_dotenv
import os

load_dotenv()

class JpHolidayStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get environment variables
        table_name = os.getenv('DYNAMODB_TABLE_NAME')
        lambda_memory = int(os.getenv('LAMBDA_MEMORY_SIZE'))
        lambda_timeout = int(os.getenv('LAMBDA_TIMEOUT'))
        stage = os.getenv('STAGE')
        jpholiday_layer_arn = os.getenv('JPHOLIDAY_LAYER_ARN')

        # DynamoDB table
        holiday_table = dynamodb.Table(
            self, "HolidaysTable",
            table_name=f"{table_name}",
            partition_key=dynamodb.Attribute(
                name="date",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="name",
                type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY if stage == 'dev' else RemovalPolicy.RETAIN,
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        # Lambda Layer
        jpholiday_layer = _lambda.LayerVersion.from_layer_version_arn(
            self, "JpHolidayLayer",
            layer_version_arn=jpholiday_layer_arn
        )

        # Lambda function
        holiday_function = _lambda.Function(
            self, "JpHolidayFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(lambda_timeout),
            memory_size=lambda_memory,
            layers=[jpholiday_layer],
            environment={
                "TABLE_NAME": holiday_table.table_name,
                "STAGE": stage
            }
        )

        # Grant permissions
        holiday_table.grant_write_data(holiday_function)

        # CloudWatch Events Rule (EventBridge)
        events.Rule(
            self, "MonthlyRule",
            schedule=events.Schedule.cron(
                minute="0",
                hour="0",
                day="1",
                month="*",
                year="*"
            ),
            targets=[targets.LambdaFunction(holiday_function)]
        )
