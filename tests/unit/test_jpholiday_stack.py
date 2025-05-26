"""Unit tests for JpHolidayStack."""

import os
from unittest.mock import patch

import aws_cdk as core
import aws_cdk.assertions as assertions
import pytest

from jpholiday.jpholiday_stack import JpHolidayStack


class TestJpHolidayStack:
    """Test class for JpHolidayStack."""

    @patch.dict(
        os.environ,
        {
            "DYNAMODB_TABLE_NAME": "test-holidays",
            "LAMBDA_MEMORY_SIZE": "128",
            "LAMBDA_TIMEOUT": "30",
            "STAGE": "test",
            "JPHOLIDAY_LAYER_ARN": "arn:aws:lambda:ap-northeast-1:123456789012:layer:jpholiday-layer:1",
        },
    )
    def test_dynamodb_table_created(self):
        """Test that DynamoDB table is created correctly."""
        app = core.App()
        stack = JpHolidayStack(app, "jp-holiday-test")
        template = assertions.Template.from_stack(stack)

        # Check DynamoDB table existence
        template.has_resource_properties(
            "AWS::DynamoDB::Table",
            {
                "TableName": "test-holidays",
                "BillingMode": "PAY_PER_REQUEST",
                "AttributeDefinitions": [
                    {"AttributeName": "date", "AttributeType": "S"},
                    {"AttributeName": "name", "AttributeType": "S"},
                ],
                "KeySchema": [
                    {"AttributeName": "date", "KeyType": "HASH"},
                    {"AttributeName": "name", "KeyType": "RANGE"},
                ],
            },
        )

    @patch.dict(
        os.environ,
        {
            "DYNAMODB_TABLE_NAME": "test-holidays",
            "LAMBDA_MEMORY_SIZE": "256",
            "LAMBDA_TIMEOUT": "60",
            "STAGE": "test",
            "JPHOLIDAY_LAYER_ARN": "arn:aws:lambda:ap-northeast-1:123456789012:layer:jpholiday-layer:1",
        },
    )
    def test_lambda_function_created(self):
        """Test that Lambda function is created correctly."""
        app = core.App()
        stack = JpHolidayStack(app, "jp-holiday-test")
        template = assertions.Template.from_stack(stack)

        # Check Lambda function existence
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {
                "Runtime": "python3.9",
                "Handler": "index.handler",
                "MemorySize": 256,
                "Timeout": 60,
                "Environment": {"Variables": {"STAGE": "test"}},
            },
        )

    @patch.dict(
        os.environ,
        {
            "DYNAMODB_TABLE_NAME": "test-holidays",
            "LAMBDA_MEMORY_SIZE": "128",
            "LAMBDA_TIMEOUT": "30",
            "STAGE": "test",
            "JPHOLIDAY_LAYER_ARN": "arn:aws:lambda:ap-northeast-1:123456789012:layer:jpholiday-layer:1",
        },
    )
    def test_eventbridge_rule_created(self):
        """Test that EventBridge rule is created correctly."""
        app = core.App()
        stack = JpHolidayStack(app, "jp-holiday-test")
        template = assertions.Template.from_stack(stack)

        # Check EventBridge rule existence (executed on 1st day of each month at 0:00)
        template.has_resource_properties(
            "AWS::Events::Rule",
            {"ScheduleExpression": "cron(0 0 1 * ? *)", "State": "ENABLED"},
        )

    @patch.dict(
        os.environ,
        {
            "DYNAMODB_TABLE_NAME": "test-holidays",
            "LAMBDA_MEMORY_SIZE": "128",
            "LAMBDA_TIMEOUT": "30",
            "STAGE": "dev",  # dev environment
            "JPHOLIDAY_LAYER_ARN": "arn:aws:lambda:ap-northeast-1:123456789012:layer:jpholiday-layer:1",
        },
    )
    def test_removal_policy_dev_environment(self):
        """Test that DynamoDB table RemovalPolicy is DESTROY in dev environment."""
        app = core.App()
        stack = JpHolidayStack(app, "jp-holiday-test")
        template = assertions.Template.from_stack(stack)

        # Check DynamoDB table deletion policy (dev environment)
        template.has_resource_properties("AWS::DynamoDB::Table", {"DeletionPolicy": "Delete"})

    @patch.dict(
        os.environ,
        {
            "DYNAMODB_TABLE_NAME": "test-holidays",
            "LAMBDA_MEMORY_SIZE": "128",
            "LAMBDA_TIMEOUT": "30",
            "STAGE": "prod",  # prod environment
            "JPHOLIDAY_LAYER_ARN": "arn:aws:lambda:ap-northeast-1:123456789012:layer:jpholiday-layer:1",
        },
    )
    def test_removal_policy_prod_environment(self):
        """Test that DynamoDB table RemovalPolicy is RETAIN in prod environment."""
        app = core.App()
        stack = JpHolidayStack(app, "jp-holiday-test")
        template = assertions.Template.from_stack(stack)

        # Check DynamoDB table deletion policy (prod environment)
        template.has_resource_properties("AWS::DynamoDB::Table", {"DeletionPolicy": "Retain"})

    def test_missing_environment_variables(self):
        """Test error handling when environment variables are not set."""
        app = core.App()

        # Try to create stack without environment variables
        with pytest.raises(ValueError):
            JpHolidayStack(app, "jp-holiday-test")

    @patch.dict(
        os.environ,
        {
            "DYNAMODB_TABLE_NAME": "test-holidays",
            "LAMBDA_MEMORY_SIZE": "128",
            "LAMBDA_TIMEOUT": "30",
            "STAGE": "test",
            "JPHOLIDAY_LAYER_ARN": "arn:aws:lambda:ap-northeast-1:123456789012:layer:jpholiday-layer:1",
        },
    )
    def test_iam_permissions(self):
        """Test that Lambda function has appropriate permissions to DynamoDB."""
        app = core.App()
        stack = JpHolidayStack(app, "jp-holiday-test")
        template = assertions.Template.from_stack(stack)

        # Check IAM role existence
        template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "AssumeRolePolicyDocument": {
                    "Statement": [
                        {
                            "Action": "sts:AssumeRole",
                            "Effect": "Allow",
                            "Principal": {"Service": "lambda.amazonaws.com"},
                        }
                    ]
                }
            },
        )

        # Check DynamoDB write permissions
        template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": {
                    "Statement": assertions.Match.array_with(
                        [
                            {
                                "Action": [
                                    "dynamodb:BatchWriteItem",
                                    "dynamodb:PutItem",
                                    "dynamodb:UpdateItem",
                                    "dynamodb:DeleteItem",
                                ],
                                "Effect": "Allow",
                            }
                        ]
                    )
                }
            },
        )
