"""Unit tests for JpHolidayStack."""

import importlib.util
import os
import sys
from pathlib import Path
from unittest.mock import patch

import aws_cdk as core
import aws_cdk.assertions as assertions
import pytest

# Direct import of the stack module to avoid package conflicts
project_root = Path(__file__).parent.parent.parent
stack_module_path = project_root / "jpholiday" / "jpholiday_stack.py"

spec = importlib.util.spec_from_file_location("jpholiday_stack", stack_module_path)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load spec from {stack_module_path}")

jpholiday_stack_module = importlib.util.module_from_spec(spec)
sys.modules["jpholiday_stack"] = jpholiday_stack_module
spec.loader.exec_module(jpholiday_stack_module)

JpHolidayStack = jpholiday_stack_module.JpHolidayStack


@pytest.fixture
def test_env_vars():
    """Common environment variables for testing."""
    return {
        "DYNAMODB_TABLE_NAME": "test-holidays",
        "LAMBDA_MEMORY_SIZE": "128",
        "LAMBDA_TIMEOUT": "30",
        "STAGE": "test",
        "JPHOLIDAY_LAYER_ARN": "arn:aws:lambda:ap-northeast-1:123456789012:layer:jpholiday-layer:1",
    }


@pytest.fixture
def app():
    """CDK App instance for testing."""
    return core.App()


class TestJpHolidayStack:
    """Test class for JpHolidayStack."""

    def test_stack_creation_with_valid_env_vars(self, app, test_env_vars):
        """Test that stack creates successfully with valid environment variables."""
        with patch.dict(os.environ, test_env_vars):
            stack = JpHolidayStack(app, "jp-holiday-test")
            template = assertions.Template.from_stack(stack)

            # Verify stack contains expected resources
            template.resource_count_is("AWS::DynamoDB::Table", 1)
            template.resource_count_is("AWS::Lambda::Function", 1)
            template.resource_count_is("AWS::Events::Rule", 1)

    def test_dynamodb_table_configuration(self, app, test_env_vars):
        """Test DynamoDB table is configured correctly."""
        with patch.dict(os.environ, test_env_vars):
            stack = JpHolidayStack(app, "jp-holiday-test")
            template = assertions.Template.from_stack(stack)

            template.has_resource_properties(
                "AWS::DynamoDB::Table",
                {
                    "TableName": "test-holidays",
                    "BillingMode": "PAY_PER_REQUEST",
                    "KeySchema": [
                        {"AttributeName": "date", "KeyType": "HASH"},
                        {"AttributeName": "name", "KeyType": "RANGE"},
                    ],
                },
            )

    def test_lambda_function_configuration(self, app, test_env_vars):
        """Test Lambda function is configured correctly."""
        with patch.dict(os.environ, test_env_vars):
            stack = JpHolidayStack(app, "jp-holiday-test")
            template = assertions.Template.from_stack(stack)

            template.has_resource_properties(
                "AWS::Lambda::Function",
                {
                    "Runtime": "python3.9",
                    "Handler": "index.handler",
                    "MemorySize": 128,
                    "Timeout": 30,
                },
            )

    def test_eventbridge_schedule(self, app, test_env_vars):
        """Test EventBridge rule is scheduled correctly."""
        with patch.dict(os.environ, test_env_vars):
            stack = JpHolidayStack(app, "jp-holiday-test")
            template = assertions.Template.from_stack(stack)

            # Monthly execution on 1st day at midnight
            template.has_resource_properties(
                "AWS::Events::Rule",
                {
                    "ScheduleExpression": "cron(0 0 1 * ? *)",
                    "State": "ENABLED",
                },
            )

    @pytest.mark.parametrize(
        "stage,expected_deletion_policy",
        [
            ("dev", "Delete"),
            ("prod", "Retain"),
        ],
    )
    def test_removal_policy_by_stage(self, app, test_env_vars, stage, expected_deletion_policy):
        """Test DynamoDB table removal policy varies by environment stage."""
        test_env_vars["STAGE"] = stage
        with patch.dict(os.environ, test_env_vars):
            stack = JpHolidayStack(app, "jp-holiday-test")
            template = assertions.Template.from_stack(stack)

            # DeletionPolicy is set at resource level, not in Properties
            template.has_resource(
                "AWS::DynamoDB::Table",
                {
                    "DeletionPolicy": expected_deletion_policy,
                    "Properties": {
                        "TableName": "test-holidays",
                        "BillingMode": "PAY_PER_REQUEST",
                    },
                },
            )

    @pytest.mark.parametrize(
        "missing_var",
        [
            "DYNAMODB_TABLE_NAME",
            "LAMBDA_MEMORY_SIZE",
            "LAMBDA_TIMEOUT",
            "STAGE",
            "JPHOLIDAY_LAYER_ARN",
        ],
    )
    def test_missing_required_environment_variables(self, app, test_env_vars, missing_var):
        """Test that missing required environment variables raise ValueError."""
        # Remove one required environment variable
        incomplete_env = test_env_vars.copy()
        del incomplete_env[missing_var]

        with patch.dict(os.environ, incomplete_env, clear=True):
            with pytest.raises(ValueError, match=f"{missing_var} environment variable is required"):
                JpHolidayStack(app, "jp-holiday-test")

    def test_lambda_has_dynamodb_permissions(self, app, test_env_vars):
        """Test Lambda function has necessary DynamoDB write permissions."""
        with patch.dict(os.environ, test_env_vars):
            stack = JpHolidayStack(app, "jp-holiday-test")
            template = assertions.Template.from_stack(stack)

            # Check that IAM policy includes DynamoDB write actions
            template.has_resource_properties(
                "AWS::IAM::Policy",
                {
                    "PolicyDocument": {
                        "Statement": assertions.Match.array_with(
                            [
                                {
                                    "Action": assertions.Match.array_with(
                                        [
                                            "dynamodb:BatchWriteItem",
                                            "dynamodb:PutItem",
                                        ]
                                    ),
                                    "Effect": "Allow",
                                    "Resource": assertions.Match.any_value(),
                                }
                            ]
                        )
                    }
                },
            )
