import aws_cdk as core
import aws_cdk.assertions as assertions
import pytest
import os
from unittest.mock import patch

from jpholiday.jpholiday_stack import JpHolidayStack


class TestJpHolidayStack:
    """JpHolidayStackのテストクラス"""
    
    @patch.dict(os.environ, {
        'DYNAMODB_TABLE_NAME': 'test-holidays',
        'LAMBDA_MEMORY_SIZE': '128',
        'LAMBDA_TIMEOUT': '30',
        'STAGE': 'test',
        'JPHOLIDAY_LAYER_ARN': 'arn:aws:lambda:ap-northeast-1:123456789012:layer:jpholiday-layer:1'
    })
    def test_dynamodb_table_created(self):
        """DynamoDBテーブルが正しく作成されることをテスト"""
        app = core.App()
        stack = JpHolidayStack(app, "jp-holiday-test")
        template = assertions.Template.from_stack(stack)

        # DynamoDBテーブルの存在確認
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "TableName": "test-holidays",
            "BillingMode": "PAY_PER_REQUEST",
            "AttributeDefinitions": [
                {
                    "AttributeName": "date",
                    "AttributeType": "S"
                },
                {
                    "AttributeName": "name", 
                    "AttributeType": "S"
                }
            ],
            "KeySchema": [
                {
                    "AttributeName": "date",
                    "KeyType": "HASH"
                },
                {
                    "AttributeName": "name",
                    "KeyType": "RANGE"
                }
            ]
        })

    @patch.dict(os.environ, {
        'DYNAMODB_TABLE_NAME': 'test-holidays',
        'LAMBDA_MEMORY_SIZE': '256',
        'LAMBDA_TIMEOUT': '60',
        'STAGE': 'test',
        'JPHOLIDAY_LAYER_ARN': 'arn:aws:lambda:ap-northeast-1:123456789012:layer:jpholiday-layer:1'
    })
    def test_lambda_function_created(self):
        """Lambda関数が正しく作成されることをテスト"""
        app = core.App()
        stack = JpHolidayStack(app, "jp-holiday-test")
        template = assertions.Template.from_stack(stack)

        # Lambda関数の存在確認
        template.has_resource_properties("AWS::Lambda::Function", {
            "Runtime": "python3.9",
            "Handler": "index.handler",
            "MemorySize": 256,
            "Timeout": 60,
            "Environment": {
                "Variables": {
                    "STAGE": "test"
                }
            }
        })

    @patch.dict(os.environ, {
        'DYNAMODB_TABLE_NAME': 'test-holidays',
        'LAMBDA_MEMORY_SIZE': '128',
        'LAMBDA_TIMEOUT': '30',
        'STAGE': 'test',
        'JPHOLIDAY_LAYER_ARN': 'arn:aws:lambda:ap-northeast-1:123456789012:layer:jpholiday-layer:1'
    })
    def test_eventbridge_rule_created(self):
        """EventBridgeルールが正しく作成されることをテスト"""
        app = core.App()
        stack = JpHolidayStack(app, "jp-holiday-test")
        template = assertions.Template.from_stack(stack)

        # EventBridgeルールの存在確認（毎月1日0時実行）
        template.has_resource_properties("AWS::Events::Rule", {
            "ScheduleExpression": "cron(0 0 1 * ? *)",
            "State": "ENABLED"
        })

    @patch.dict(os.environ, {
        'DYNAMODB_TABLE_NAME': 'test-holidays',
        'LAMBDA_MEMORY_SIZE': '128', 
        'LAMBDA_TIMEOUT': '30',
        'STAGE': 'dev',  # dev環境
        'JPHOLIDAY_LAYER_ARN': 'arn:aws:lambda:ap-northeast-1:123456789012:layer:jpholiday-layer:1'
    })
    def test_removal_policy_dev_environment(self):
        """dev環境でDynamoDBテーブルのRemovalPolicyがDESTROYになることをテスト"""
        app = core.App()
        stack = JpHolidayStack(app, "jp-holiday-test")
        template = assertions.Template.from_stack(stack)

        # DynamoDBテーブルの削除ポリシー確認（dev環境）
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "DeletionPolicy": "Delete"
        })

    @patch.dict(os.environ, {
        'DYNAMODB_TABLE_NAME': 'test-holidays',
        'LAMBDA_MEMORY_SIZE': '128',
        'LAMBDA_TIMEOUT': '30', 
        'STAGE': 'prod',  # prod環境
        'JPHOLIDAY_LAYER_ARN': 'arn:aws:lambda:ap-northeast-1:123456789012:layer:jpholiday-layer:1'
    })
    def test_removal_policy_prod_environment(self):
        """prod環境でDynamoDBテーブルのRemovalPolicyがRETAINになることをテスト"""
        app = core.App()
        stack = JpHolidayStack(app, "jp-holiday-test")
        template = assertions.Template.from_stack(stack)

        # DynamoDBテーブルの削除ポリシー確認（prod環境）
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "DeletionPolicy": "Retain"
        })

    def test_missing_environment_variables(self):
        """環境変数が設定されていない場合のエラーハンドリングをテスト"""
        app = core.App()
        
        # 環境変数なしでスタック作成を試行
        with pytest.raises((KeyError, TypeError)):
            JpHolidayStack(app, "jp-holiday-test")

    @patch.dict(os.environ, {
        'DYNAMODB_TABLE_NAME': 'test-holidays',
        'LAMBDA_MEMORY_SIZE': '128',
        'LAMBDA_TIMEOUT': '30',
        'STAGE': 'test',
        'JPHOLIDAY_LAYER_ARN': 'arn:aws:lambda:ap-northeast-1:123456789012:layer:jpholiday-layer:1'
    })
    def test_iam_permissions(self):
        """Lambda関数がDynamoDBへの適切な権限を持つことをテスト"""
        app = core.App()
        stack = JpHolidayStack(app, "jp-holiday-test")
        template = assertions.Template.from_stack(stack)

        # IAMロールの存在確認
        template.has_resource_properties("AWS::IAM::Role", {
            "AssumeRolePolicyDocument": {
                "Statement": [
                    {
                        "Action": "sts:AssumeRole",
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "lambda.amazonaws.com"
                        }
                    }
                ]
            }
        })

        # DynamoDB書き込み権限の確認
        template.has_resource_properties("AWS::IAM::Policy", {
            "PolicyDocument": {
                "Statement": assertions.Match.array_with([
                    {
                        "Action": [
                            "dynamodb:BatchWriteItem",
                            "dynamodb:PutItem",
                            "dynamodb:UpdateItem",
                            "dynamodb:DeleteItem"
                        ],
                        "Effect": "Allow"
                    }
                ])
            }
        })