# 日本の祝日カレンダー AWS CDK

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg?logo=python&logoColor=white)](https://www.python.org)
[![AWS CDK](https://img.shields.io/badge/AWS%20CDK-v2.162+-orange.svg?logo=amazon-aws&logoColor=white)](https://aws.amazon.com/cdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-FF9900?logo=aws-lambda&logoColor=white)](https://aws.amazon.com/lambda/)
[![Amazon DynamoDB](https://img.shields.io/badge/Amazon-DynamoDB-4053D6?logo=amazon-dynamodb&logoColor=white)](https://aws.amazon.com/dynamodb/)
[![Amazon EventBridge](https://img.shields.io/badge/Amazon-EventBridge-FF4F8B?logo=amazon-aws&logoColor=white)](https://aws.amazon.com/eventbridge/)
[![Infrastructure as Code](https://img.shields.io/badge/Infrastructure-as%20Code-blue?logo=terraform&logoColor=white)](https://aws.amazon.com/what-is/iac/)

[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/yourusername/jp-holiday-calendar/graphs/commit-activity)
[![GitHub last commit](https://img.shields.io/github/last-commit/yourusername/jp-holiday-calendar)](https://github.com/yourusername/jp-holiday-calendar/commits/main)
[![GitHub issues](https://img.shields.io/github/issues/yourusername/jp-holiday-calendar)](https://github.com/yourusername/jp-holiday-calendar/issues)

日本の祝日を自動的に取得し、Amazon DynamoDBに保存するサーバーレスアプリケーションです。毎月1日に自動実行され、常に最新の祝日データを維持します。

## 🏗️ アーキテクチャ概要

このアプリケーションは以下のAWSサービスを使用してサーバーレスアーキテクチャを構成しています：

- **AWS Lambda**: jpholidayライブラリを使用して日本の祝日データを取得・処理
- **Amazon DynamoDB**: 祝日情報を効率的に保存するNoSQLデータベース
- **Amazon EventBridge**: 毎月1日にLambda関数を自動実行するスケジューラー
- **AWS Lambda Layers**: jpholidayライブラリを効率的に管理・配布
- **AWS CDK**: Infrastructure as Codeでリソースを管理・デプロイ

## ✨ 主な機能

- **自動祝日取得**: 現在日から365日先までの日本の祝日を自動取得
- **定期更新**: 毎月1日に自動実行され、データを常に最新状態に保持
- **スケーラブル設計**: サーバーレスアーキテクチャによる高い可用性とコスト効率
- **環境分離**: 開発・本番環境の設定を環境変数で管理
- **Infrastructure as Code**: AWS CDKによる再現可能なインフラ管理

## 📋 前提条件

以下のツールとサービスが必要です：

- [AWSアカウント](https://aws.amazon.com/jp/account/) - 適切なIAM権限を持つ
- [AWS CLI](https://aws.amazon.com/jp/cli/) v2.x - 認証情報が設定済み
- [Python](https://www.python.org/) 3.9以上
- [Node.js](https://nodejs.org/) v16以上（CDK CLI・pre-commitフック用）
- [AWS CDK Toolkit](https://docs.aws.amazon.com/cdk/latest/guide/cli.html) - `npm install -g aws-cdk`

## 🚀 セットアップ手順

### 1. プロジェクトのクローン

```bash
git clone https://github.com/yourusername/jp-holiday-calendar.git
cd jp-holiday-calendar
```

### 2. Python仮想環境の作成と有効化

```bash
# 仮想環境の作成
python -m venv .venv

# 仮想環境の有効化
# macOS/Linux:
source .venv/bin/activate
# Windows:
source.bat
```

### 3. 依存関係のインストール

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 開発用（テスト実行用）
```

### 4. 環境変数の設定

プロジェクトルートに`.env`ファイルを作成し、以下の内容を設定してください：

```env
# DynamoDB設定
DYNAMODB_TABLE_NAME=jp-holidays

# Lambda設定
LAMBDA_MEMORY_SIZE=128
LAMBDA_TIMEOUT=30

# 環境設定
STAGE=dev  # dev または prod

# Lambda Layer ARN（後述の手順で作成）
JPHOLIDAY_LAYER_ARN=arn:aws:lambda:ap-northeast-1:123456789012:layer:jpholiday-layer:1

# AWS設定
AWS_ACCOUNT=123456789012
AWS_REGION=ap-northeast-1
```

### 5. 開発環境の追加設定（推奨）

品質保証のため、pre-commitフックの設定を推奨します：

```bash
# Huskyのセットアップ（Node.jsが必要）
npm install

# pre-commitフックの有効化
npm run prepare

# 手動でpre-commitフックをテスト
.husky/pre-commit
```

pre-commitフックは以下を自動実行します：
- コードフォーマット（Black、isort、Ruff）
- コード品質チェック（Ruff、mypy）
- ユニットテスト（pytest）

## 🔧 jpholiday Lambda Layerの作成

Lambda関数で外部ライブラリ（jpholiday）を使用するため、Lambda Layerを事前に作成する必要があります。

### 方法1: AWS CLIを使用

```bash
# 1. 作業ディレクトリの作成
mkdir -p /tmp/lambda-layer/python

# 2. jpholidayライブラリのインストール
pip install jpholiday -t /tmp/lambda-layer/python

# 3. ZIPファイルの作成
cd /tmp/lambda-layer
zip -r jpholiday-layer.zip python/

# 4. Lambda Layerの作成
aws lambda publish-layer-version \
  --layer-name jpholiday-layer \
  --description "jpholiday library for Japanese holidays" \
  --compatible-runtimes python3.9 \
  --zip-file fileb://jpholiday-layer.zip \
  --region ap-northeast-1

# 5. 出力されたLayerVersionArnを.envファイルのJPHOLIDAY_LAYER_ARNに設定
```

### 方法2: AWS Consoleを使用

1. AWS Lambda コンソール → 「レイヤー」→「レイヤーの作成」
2. レイヤー名: `jpholiday-layer`
3. 上記で作成したZIPファイルをアップロード
4. 互換性のあるランタイム: `Python 3.9`
5. 作成後、ARNを`.env`ファイルに設定

## 🚀 デプロイ

### 1. CDK環境のブートストラップ（初回のみ）

```bash
cdk bootstrap aws://YOUR_ACCOUNT_ID/YOUR_REGION
```

### 2. スタックのデプロイ

```bash
# デプロイ前の差分確認
cdk diff

# デプロイ実行
cdk deploy
```

デプロイが完了すると、以下のリソースが作成されます：
- DynamoDBテーブル: `jp-holidays-dev`
- Lambda関数: `JpHolidayStack-dev-JpHolidayFunction`
- EventBridgeルール: 毎月1日0時に実行

## 🏗️ プロジェクト構造

```
jp-holiday-calendar/
├── app.py                           # CDKアプリケーションのエントリーポイント
├── jpholiday/
│   ├── __init__.py
│   └── jpholiday_stack.py          # メインのCDKスタック定義
├── lambda/
│   └── index.py                    # Lambda関数のコード
├── tests/
│   ├── __init__.py
│   └── unit/
│       ├── __init__.py
│       └── test_jpholiday_stack.py # ユニットテスト
├── .husky/
│   └── pre-commit                  # Git pre-commitフック
├── requirements.txt                # 本番依存関係
├── requirements-dev.txt           # 開発依存関係
├── package.json                   # Node.js依存関係（開発ツール用）
├── pyproject.toml                 # Python設定（Black、isort、Ruff、mypy）
├── cdk.json                       # CDK設定
├── .env                          # 環境変数（要作成）
├── .env.example                  # 環境変数の設定例
└── README.md
```

## 📊 DynamoDBテーブル構造

祝日データは以下の構造でDynamoDBに保存されます：

| 属性名 | 型 | キー | 説明 | 例 |
|--------|----|----|------|-----|
| `date` | String | パーティションキー | 祝日の日付（YYYY-MM-DD形式） | `"2024-01-01"` |
| `name` | String | ソートキー | 祝日の名前（日本語） | `"元日"` |

### クエリ例

```python
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('jp-holidays-dev')

# 特定の日付の祝日を取得
response = table.get_item(
    Key={
        'date': '2024-01-01',
        'name': '元日'
    }
)

# 日付範囲での祝日を取得
response = table.query(
    KeyConditionExpression='#date BETWEEN :start_date AND :end_date',
    ExpressionAttributeNames={
        '#date': 'date'
    },
    ExpressionAttributeValues={
        ':start_date': '2024-01-01',
        ':end_date': '2024-12-31'
    }
)
```

## 🧪 テスト実行

```bash
# 全テストの実行
pytest

# カバレッジ付きでテスト実行
pytest --cov=jpholiday

# 詳細出力でテスト実行
pytest -v

# 特定のテストファイルのみ実行
pytest tests/unit/test_jpholiday_stack.py -v
```

## 🔧 開発・運用コマンド

### 開発ワークフロー

```bash
# 開発開始時
source .venv/bin/activate  # 仮想環境の有効化

# コード品質チェック（手動実行）
npm run lint               # リント・型チェック
npm run format            # コードフォーマット
npm run test              # テスト実行

# コミット（pre-commitフックが自動実行）
git add .
git commit -m "feat: add new feature"
```

### CDKコマンド

```bash
# スタック一覧の表示
cdk ls

# CloudFormationテンプレートの生成・表示
cdk synth

# デプロイ前の差分確認
cdk diff

# スタックのデプロイ
cdk deploy

# スタックの削除
cdk destroy

# CDKドキュメントを開く
cdk docs
```

### Lambda関数の手動実行

```bash
# AWS CLIでLambda関数を直接実行
aws lambda invoke \
  --function-name JpHolidayStack-dev-JpHolidayFunction \
  --payload '{}' \
  --region ap-northeast-1 \
  response.json

cat response.json
```

### ログの確認

```bash
# CloudWatch Logsでログを確認
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/JpHolidayStack"

# 最新のログストリームを確認
aws logs describe-log-streams \
  --log-group-name "/aws/lambda/JpHolidayStack-dev-JpHolidayFunction" \
  --order-by LastEventTime \
  --descending \
  --max-items 1
```

## 🔄 実行スケジュール

- **実行頻度**: 毎月1日 0時0分（UTC）
- **処理内容**: 実行日から365日先までの日本の祝日を取得・更新
- **実行時間**: 通常30秒以内

## 💰 コスト見積もり

月間推定コスト（東京リージョン）：

- **Lambda**: $0.01未満（月1回実行、128MB、30秒以内）
- **DynamoDB**: $0.25未満（約50レコード、PAY_PER_REQUEST）
- **EventBridge**: $0.01未満（月1回のスケジュール実行）
- **Lambda Layer**: 無料

**合計**: 月額$0.30未満

## 🔒 セキュリティ考慮事項

- Lambda関数にはDynamoDBへの最小限の書き込み権限のみ付与
- 環境変数は`.env`ファイルで管理（`.gitignore`に含まれる）
- VPC内での実行は不要（パブリックAPI使用）
- CloudWatch Logsで実行履歴を追跡可能

## 🚨 トラブルシューティング

### よくある問題と解決方法

#### 1. Lambda Layer ARNが正しくない
```
Error: Layer version does not exist or is not accessible
```
**解決方法**: `.env`ファイルのJPHOLIDAY_LAYER_ARNを確認し、正しいARNを設定してください。

#### 2. 権限エラー
```
AccessDeniedException: User is not authorized to perform: dynamodb:PutItem
```
**解決方法**: AWS CLIの認証情報を確認し、必要なIAM権限があることを確認してください。

#### 3. タイムアウトエラー
```
Task timed out after 30.00 seconds
```
**解決方法**: `.env`ファイルでLAMBDA_TIMEOUTを60に増やしてください。

## 🔄 更新・メンテナンス

### 依存関係の更新

```bash
# Python依存関係の確認と更新
pip list --outdated
pip freeze > requirements.txt

# 開発ツールの更新
pip install --upgrade pytest black isort ruff mypy

# CDKの更新
npm update -g aws-cdk
pip install --upgrade aws-cdk-lib

# Node.js開発依存関係の更新
npm update --save-dev
```

### Lambda Layerの更新

新しいバージョンのjpholidayライブラリがリリースされた場合：

1. 新しいLayerを作成（バージョン番号が自動増加）
2. `.env`ファイルでJPHOLIDAY_LAYER_ARNを更新
3. `cdk deploy`で再デプロイ

## 🧹 クリーンアップ

全てのリソースを削除する場合：

```bash
# スタックの削除
cdk destroy

# Lambda Layerの削除（必要に応じて）
aws lambda delete-layer-version \
  --layer-name jpholiday-layer \
  --version-number 1
```

## 📝 ライセンス

[MIT License](LICENSE)

