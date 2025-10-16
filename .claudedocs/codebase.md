# コードベース構造

## ディレクトリ構造

```
jpholiday/
├── .claudedocs/              # Claudeドキュメント
│   ├── overview.md          # プロジェクト概要
│   ├── architecture.md      # アーキテクチャ詳細
│   ├── development.md       # 開発ガイド
│   └── codebase.md          # このファイル
├── .github/                 # GitHub設定
│   └── workflows/           # GitHub Actions（もしあれば）
├── .husky/                  # Git hooks
│   └── pre-commit           # Pre-commitフック
├── .vscode/                 # VS Code設定
│   └── settings.json        # エディタ設定
├── jpholiday/              # CDKスタック定義
│   ├── __init__.py
│   └── jpholiday_stack.py   # メインスタック
├── lambda/                  # Lambda関数コード
│   └── index.py             # Lambda handler
├── tests/                   # テストコード
│   ├── __init__.py
│   └── unit/
│       ├── __init__.py
│       └── test_jpholiday_stack.py
├── app.py                   # CDKエントリーポイント
├── cdk.json                 # CDK設定
├── pyproject.toml          # Python ツール設定
├── requirements.txt         # 本番依存関係
├── requirements-dev.txt     # 開発依存関係
├── package.json            # Node.js設定
├── .env.example            # 環境変数テンプレート
├── .gitignore              # Git除外設定
└── README.md               # プロジェクトドキュメント
```

## 主要ファイル詳細

### app.py (18行)

**役割:** CDKアプリケーションのエントリーポイント

**処理フロー:**
```python
1. dotenvで.envファイル読み込み
2. 環境変数からAWSアカウント・リージョン取得
3. CDK Appインスタンス作成
4. JpHolidayStackインスタンス化
5. app.synth()でCloudFormation生成
```

**重要な箇所:**
```python
# app.py:10-16
env = Environment(
    account=os.getenv("AWS_ACCOUNT"),
    region=os.getenv("AWS_REGION")
)

JpHolidayStack(app, "JpHolidayStack", env=env)
```

**依存関係:**
- aws_cdk: CDKコアライブラリ
- dotenv: 環境変数読み込み
- jpholiday.jpholiday_stack: スタック定義

---

### jpholiday/jpholiday_stack.py (94行)

**役割:** AWSリソースのCDK定義

**クラス:** `JpHolidayStack(Stack)`

**主要メソッド:**

#### `__init__(scope, construct_id, **kwargs)` (94行)

**処理フロー:**
```python
1. 環境変数バリデーション
2. DynamoDBテーブル作成
3. Lambda Layer参照
4. Lambda関数作成
5. EventBridgeルール作成
6. 権限設定
```

**環境変数バリデーション (jpholiday/jpholiday_stack.py:20-28):**
```python
required_env_vars = [
    "DYNAMODB_TABLE_NAME",
    "LAMBDA_MEMORY_SIZE",
    "LAMBDA_TIMEOUT",
    "STAGE",
    "JPHOLIDAY_LAYER_ARN",
]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {missing_vars}")
```

**DynamoDBテーブル (jpholiday/jpholiday_stack.py:30-41):**
```python
table = dynamodb.Table(
    self,
    "JpHolidayTable",
    table_name=os.getenv("DYNAMODB_TABLE_NAME"),
    partition_key=dynamodb.Attribute(
        name="date", type=dynamodb.AttributeType.STRING
    ),
    sort_key=dynamodb.Attribute(
        name="name", type=dynamodb.AttributeType.STRING
    ),
    billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
    removal_policy=removal_policy,
)
```

**Lambda関数 (jpholiday/jpholiday_stack.py:48-64):**
```python
lambda_function = _lambda.Function(
    self,
    "JpHolidayFunction",
    runtime=_lambda.Runtime.PYTHON_3_9,
    handler="index.handler",
    code=_lambda.Code.from_asset("lambda"),
    environment={
        "DYNAMODB_TABLE_NAME": table.table_name,
    },
    memory_size=int(os.getenv("LAMBDA_MEMORY_SIZE", "128")),
    timeout=Duration.seconds(int(os.getenv("LAMBDA_TIMEOUT", "30"))),
    layers=[jpholiday_layer],
)
```

**EventBridgeルール (jpholiday/jpholiday_stack.py:70-82):**
```python
rule = events.Rule(
    self,
    "JpHolidayScheduleRule",
    schedule=events.Schedule.cron(
        minute="0",
        hour="0",
        day="1",
        month="*",
        year="*",
    ),
    description="Trigger Lambda function every month on the 1st at 00:00 UTC",
)
```

**依存関係:**
- aws_cdk.Stack: CDKスタックベース
- aws_cdk.aws_dynamodb: DynamoDB
- aws_cdk.aws_lambda: Lambda
- aws_cdk.aws_events: EventBridge
- aws_cdk.aws_events_targets: Lambda ターゲット

---

### lambda/index.py (36行)

**役割:** 祝日データ取得とDynamoDB書き込み

**メインハンドラー:** `handler(event, context)`

**処理フロー:**
```python
1. 環境変数からテーブル名取得
2. DynamoDBクライアント初期化
3. 現在日から365日後を計算
4. jpholiday.between()で祝日取得
5. batch_writerで一括書き込み
6. 成功レスポンス返却
```

**重要な箇所 (lambda/index.py:8-35):**
```python
def handler(event, context):
    table_name = os.environ.get("DYNAMODB_TABLE_NAME")
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    # 今日から365日後までの祝日を取得
    start_date = datetime.date.today()
    end_date = start_date + datetime.timedelta(days=365)
    holidays = jpholiday.between(start_date, end_date)

    # DynamoDBに書き込み
    with table.batch_writer() as batch:
        for holiday_date, holiday_name in holidays:
            batch.put_item(
                Item={
                    "date": holiday_date.strftime("%Y-%m-%d"),
                    "name": holiday_name,
                }
            )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Holidays data written to DynamoDB",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
        }, ensure_ascii=False)
    }
```

**依存関係:**
- boto3: AWS SDK
- jpholiday: 祝日取得ライブラリ（Lambda Layerから）

**環境変数:**
- `DYNAMODB_TABLE_NAME`: 書き込み先テーブル名

---

### tests/unit/test_jpholiday_stack.py (183行)

**役割:** CDKスタックのユニットテスト

**テストフレームワーク:** pytest

**主要テスト関数:**

#### 1. `test_dynamodb_table_created()`
```python
# DynamoDBテーブルの作成確認
テスト内容:
- テーブル名が正しいか
- PAY_PER_REQUESTモードか
- パーティションキー: date (String)
- ソートキー: name (String)
```

#### 2. `test_lambda_function_created()`
```python
# Lambda関数の作成確認
テスト内容:
- Python 3.12ランタイム
- handler: index.handler
- メモリサイズ: 128MB
- タイムアウト: 30秒
- 環境変数: TABLE_NAME, STAGE, POWERTOOLS_SERVICE_NAME, LOG_LEVEL
- Lambda Layer接続
```

#### 3. `test_eventbridge_rule_created()`
```python
# EventBridgeルールの作成確認
テスト内容:
- スケジュール式: cron(0 0 1 * ? *)
- Lambda関数がターゲット
```

#### 4. `test_dynamodb_removal_policy()`
```python
# 削除ポリシーの確認
テスト内容:
- dev環境: RemovalPolicy.DESTROY
- prod環境: RemovalPolicy.RETAIN
```

#### 5. `test_missing_environment_variables()`
```python
# 環境変数バリデーションテスト
テスト内容:
- 必須環境変数が欠けている場合にValueError
```

**テストヘルパー:**
```python
def setup_env_vars():
    """必要な環境変数を設定"""
    os.environ["DYNAMODB_TABLE_NAME"] = "test-table"
    os.environ["LAMBDA_MEMORY_SIZE"] = "128"
    os.environ["LAMBDA_TIMEOUT"] = "30"
    os.environ["STAGE"] = "dev"
    os.environ["JPHOLIDAY_LAYER_ARN"] = "arn:aws:lambda:..."
```

**依存関係:**
- pytest: テストフレームワーク
- aws_cdk.assertions: CDKテストアサーション

---

## 設定ファイル詳細

### pyproject.toml

**Black設定:**
```toml
[tool.black]
line-length = 100
target-version = ['py312']
```

**isort設定:**
```toml
[tool.isort]
profile = "black"
line_length = 100
```

**Ruff設定:**
```toml
[tool.ruff]
line-length = 100
target-version = "py312"
exclude = ["lambda/", "cdk.out/"]
```

**mypy設定:**
```toml
[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
```

---

### cdk.json

**アプリケーション設定:**
```json
{
  "app": "python3 app.py",
  "context": {
    // 70+ CDK feature flags
    "@aws-cdk/core:enableStackNameDuplicates": true,
    "aws-cdk:enableDiffNoFail": true,
    // ...
  }
}
```

**重要なフラグ:**
- `@aws-cdk/core:enableStackNameDuplicates`: スタック名重複許可
- `aws-cdk:enableDiffNoFail`: diff失敗時も続行

---

### package.json

**スクリプト:**
```json
{
  "scripts": {
    "lint": "cd ../ && ruff check . && mypy .",
    "format": "cd ../ && black . && isort . && ruff check . --fix",
    "test": "cd ../ && pytest"
  }
}
```

**依存関係:**
```json
{
  "devDependencies": {
    "husky": "^9.1.6"
  }
}
```

---

### requirements.txt

```
aws-cdk-lib==2.162.1
constructs>=10.0.0,<11.0.0
jpholiday
python-dotenv
boto3>=1.35.0
aws-lambda-powertools>=3.3.0
```

### requirements-dev.txt

```
pytest==8.3.3
pytest-cov==6.0.0
black==24.10.0
isort==5.13.2
ruff==0.8.4
mypy==1.13.0
boto3-stubs[dynamodb]
types-boto3
pre-commit==4.0.1
```

---

## コードフロー図

### デプロイフロー

```
app.py (エントリーポイント)
  ↓
.envファイル読み込み
  ↓
JpHolidayStack初期化
  ↓
環境変数バリデーション
  ↓
AWSリソース作成
  ├─ DynamoDBテーブル
  ├─ Lambda関数
  ├─ Lambda Layer参照
  ├─ EventBridgeルール
  └─ IAM権限
  ↓
app.synth()
  ↓
CloudFormationテンプレート生成
```

### Lambda実行フロー

```
EventBridge (毎月1日 00:00 UTC)
  ↓
Lambda関数トリガー
  ↓
handler(event, context)
  ↓
環境変数取得 (DYNAMODB_TABLE_NAME)
  ↓
DynamoDBクライアント初期化
  ↓
日付範囲計算 (今日 + 365日)
  ↓
jpholiday.between() 呼び出し
  ↓
祝日リスト取得
  ↓
batch_writer で一括書き込み
  ↓
成功レスポンス返却
  ↓
CloudWatch Logsに記録
```

### テスト実行フロー

```
pytest コマンド実行
  ↓
tests/unit/test_jpholiday_stack.py 読み込み
  ↓
各テスト関数実行
  ├─ test_dynamodb_table_created
  ├─ test_lambda_function_created
  ├─ test_eventbridge_rule_created
  ├─ test_dynamodb_removal_policy
  └─ test_missing_environment_variables
  ↓
CDK Template アサーション
  ↓
テスト結果出力
```

---

## 重要な関数・クラス一覧

### app.py

| 要素 | 行 | 説明 |
|-----|---|------|
| `load_dotenv()` | 4 | .env読み込み |
| `Environment` | 10 | AWS環境定義 |
| `JpHolidayStack` | 12 | スタック初期化 |

### jpholiday/jpholiday_stack.py

| 要素 | 行 | 説明 |
|-----|---|------|
| `JpHolidayStack.__init__` | 15-94 | スタック初期化 |
| 環境変数バリデーション | 20-28 | 必須変数チェック |
| DynamoDBテーブル作成 | 30-41 | table定義 |
| Lambda Layer参照 | 43-46 | Layer ARN取得 |
| Lambda関数作成 | 48-64 | 関数定義 |
| 権限付与 | 66-68 | DynamoDB書き込み権限 |
| EventBridgeルール | 70-82 | スケジュール設定 |
| Lambda権限追加 | 84-94 | EventBridge実行権限 |

### lambda/index.py

| 要素 | 行 | 説明 |
|-----|---|------|
| `handler` | 8-36 | メインハンドラー |
| 環境変数取得 | 9 | テーブル名取得 |
| DynamoDB初期化 | 10-11 | boto3リソース |
| 日付計算 | 13-14 | 365日後まで |
| 祝日取得 | 15 | jpholiday.between |
| 一括書き込み | 17-24 | batch_writer |
| レスポンス | 26-35 | 成功レスポンス |

### tests/unit/test_jpholiday_stack.py

| 要素 | 行 | 説明 |
|-----|---|------|
| `setup_env_vars` | - | テスト用環境変数 |
| `test_dynamodb_table_created` | - | DynamoDBテスト |
| `test_lambda_function_created` | - | Lambda テスト |
| `test_eventbridge_rule_created` | - | EventBridge テスト |
| `test_dynamodb_removal_policy` | - | 削除ポリシーテスト |
| `test_missing_environment_variables` | - | バリデーションテスト |

---

## 拡張ポイント

### 新しいAWSリソースの追加

**場所:** `jpholiday/jpholiday_stack.py`

**例: SNS通知の追加**
```python
# jpholiday/jpholiday_stack.py に追加
from aws_cdk import aws_sns as sns

# __init__ 内
topic = sns.Topic(
    self,
    "JpHolidayNotificationTopic",
    display_name="JPHoliday Notifications"
)

# Lambda関数の環境変数に追加
lambda_function = _lambda.Function(
    ...
    environment={
        "DYNAMODB_TABLE_NAME": table.table_name,
        "SNS_TOPIC_ARN": topic.topic_arn,  # 追加
    },
)

# Lambda関数に権限付与
topic.grant_publish(lambda_function)
```

### Lambda関数のロジック拡張

**場所:** `lambda/index.py`

**例: エラーハンドリングの追加**
```python
def handler(event, context):
    try:
        # 既存のロジック
        ...
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
```

### 新しいテストの追加

**場所:** `tests/unit/test_jpholiday_stack.py`

**例: IAM権限のテスト**
```python
def test_lambda_has_dynamodb_permissions():
    """Lambda関数がDynamoDBへの書き込み権限を持つか確認"""
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": Match.array_with([
                    {
                        "Effect": "Allow",
                        "Action": ["dynamodb:BatchWriteItem", "dynamodb:PutItem"],
                        "Resource": Match.any_value()
                    }
                ])
            }
        }
    )
```

---

## よくある変更シナリオ

### 1. Lambda実行スケジュールの変更

**ファイル:** `jpholiday/jpholiday_stack.py:70-82`

```python
# 毎週月曜日0時に変更
schedule=events.Schedule.cron(
    minute="0",
    hour="0",
    week_day="MON",
)

# または、毎日0時に変更
schedule=events.Schedule.cron(
    minute="0",
    hour="0",
)
```

### 2. Lambdaメモリサイズの変更

**ファイル:** `.env`

```bash
LAMBDA_MEMORY_SIZE=256  # 128から256に変更
```

### 3. 祝日取得期間の変更

**ファイル:** `lambda/index.py:14`

```python
# 365日 → 730日（2年分）に変更
end_date = start_date + datetime.timedelta(days=730)
```

### 4. DynamoDBテーブル名の変更

**ファイル:** `.env`

```bash
DYNAMODB_TABLE_NAME=jpholiday-table-v2
```

再デプロイ後、古いテーブルは手動削除が必要（prod環境の場合）。

---

## コードメトリクス

```
総行数:
- app.py: 18行
- jpholiday_stack.py: 94行
- lambda/index.py: 36行
- test_jpholiday_stack.py: 183行

総計: 331行（コメント・空行含む）

言語別:
- Python: 100%

ファイル数: 10+（主要ファイル）
```
