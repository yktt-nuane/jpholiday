# アーキテクチャ詳細

## システムアーキテクチャ

```
┌─────────────────────┐
│  EventBridge Rule   │
│  (Cron: 0 0 1 * *)  │
└──────────┬──────────┘
           │ トリガー（毎月1日 00:00 UTC）
           ▼
┌─────────────────────┐
│  Lambda Function    │
│  - Python 3.9       │
│  - 128MB Memory     │
│  - 30s Timeout      │
└──────────┬──────────┘
           │
           ├─ jpholiday Layer (外部ライブラリ)
           │
           ▼
┌─────────────────────┐
│   DynamoDB Table    │
│  - PAY_PER_REQUEST  │
│  - Partition: date  │
│  - Sort: name       │
└─────────────────────┘
```

## AWSリソース詳細

### 1. Amazon EventBridge Rule

**設定:**
- スケジュール式: `cron(0 0 1 * ? *)`
- 説明: 毎月1日の午前0時（UTC）に実行
- ターゲット: Lambda関数

**目的:**
Lambda関数を定期的に起動し、祝日データの更新を自動化

### 2. AWS Lambda Function

**設定:**
```python
Runtime: Python 3.12
Handler: index.handler
Memory: 128MB
Timeout: 30秒
Environment Variables:
  - TABLE_NAME: DynamoDBテーブル名
  - STAGE: 環境（dev/prod）
  - POWERTOOLS_SERVICE_NAME: jpholiday
  - POWERTOOLS_LOG_LEVEL: ログレベル（INFO）
  - LOG_LEVEL: ログレベル（INFO）
```

**処理フロー:**
1. 現在日から365日後の日付を計算
2. `jpholiday.between()`で期間内の祝日を取得
3. DynamoDB batch_writerで一括書き込み
4. 処理結果を返却

**Lambda Layer:**
- jpholidayライブラリを含むカスタムレイヤー
- boto3（AWS SDK）の明示的な依存関係管理
- aws-lambda-powertools（構造化ログ、観測性）
- ARNは環境変数で指定: `JPHOLIDAY_LAYER_ARN`
- Python 3.12互換

**IAMロール権限:**
```json
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:BatchWriteItem",
    "dynamodb:PutItem"
  ],
  "Resource": "arn:aws:dynamodb:REGION:ACCOUNT:table/TABLE_NAME"
}
```

### 3. Amazon DynamoDB

**テーブル設定:**
```
Table Name: 環境変数で指定
Billing Mode: PAY_PER_REQUEST
Partition Key: date (String)
Sort Key: name (String)
```

**データスキーマ:**
```json
{
  "date": "2024-01-01",
  "name": "元日"
}
```

**削除ポリシー:**
- dev環境: `RemovalPolicy.DESTROY` (スタック削除時にテーブルも削除)
- prod環境: `RemovalPolicy.RETAIN` (スタック削除時もテーブルを保持)

**クエリ例:**
```python
# 特定日の祝日を取得
response = table.get_item(
    Key={
        'date': '2024-01-01',
        'name': '元日'
    }
)

# 期間内の祝日を取得
response = table.query(
    KeyConditionExpression=Key('date').between('2024-01-01', '2024-12-31')
)
```

## CDKスタック構成

### JpHolidayStack (jpholiday/jpholiday_stack.py:1-94)

**コンストラクタ引数:**
```python
JpHolidayStack(
    scope: Construct,
    construct_id: str,
    env: Environment,  # account, region
    **kwargs
)
```

**環境変数バリデーション:**
スタック初期化時に以下の環境変数の存在を確認:
- `DYNAMODB_TABLE_NAME`
- `LAMBDA_MEMORY_SIZE`
- `LAMBDA_TIMEOUT`
- `STAGE`
- `JPHOLIDAY_LAYER_ARN`

欠落している場合はエラーを発生させます。

**リソース作成順序:**
1. DynamoDBテーブル作成
2. Lambda Layerの参照
3. Lambda関数作成（環境変数でテーブル名を注入）
4. Lambda実行ロールにDynamoDB権限付与
5. EventBridgeルール作成
6. LambdaにEventBridgeからの実行権限を付与

## セキュリティ

### IAM権限

**最小権限の原則:**
- Lambda関数には必要最小限のDynamoDB権限のみ付与
- BatchWriteItemとPutItemのみ許可
- 特定のテーブルリソースに限定

### 環境変数管理

**機密情報の取り扱い:**
- `.env`ファイルで管理（.gitignoreに追加済み）
- `.env.example`をテンプレートとして提供
- AWSアカウントIDやリージョン情報を含む

## デプロイメント

### CDKによるデプロイフロー

```bash
# 1. CloudFormationテンプレート生成
cdk synth

# 2. 変更差分の確認
cdk diff

# 3. デプロイ実行
cdk deploy

# 4. リソース削除
cdk destroy
```

### CloudFormation管理

CDKが生成するCloudFormationスタック:
- スタック名: `JpHolidayStack`
- すべてのリソースがスタックで管理される
- ロールバック機能により安全なデプロイ

## モニタリング

### CloudWatch Logs

**Lambda実行ログ:**
- ロググループ: `/aws/lambda/{function-name}`
- 保持期間: デフォルト（設定可能）
- ログレベル: INFO

**監視すべき項目:**
- Lambda実行エラー
- DynamoDB書き込みエラー
- 実行時間（タイムアウト近い場合は要調整）

### CloudWatch Metrics

**Lambda メトリクス:**
- Invocations: 実行回数
- Duration: 実行時間
- Errors: エラー回数
- Throttles: スロットリング回数

**DynamoDB メトリクス:**
- ConsumedWriteCapacityUnits: 書き込み容量消費
- UserErrors: ユーザーエラー数

## スケーラビリティ

### 自動スケーリング

**Lambda:**
- 自動的にスケール（同時実行数は設定可能）
- 現在の設定では月1回の実行のためスケーリング不要

**DynamoDB:**
- PAY_PER_REQUESTモードにより自動スケール
- リクエスト量に応じて自動的に対応

### コスト最適化

**Lambda:**
- 128MBメモリ（最小値）で十分な処理速度
- 30秒タイムアウトで余裕を持たせつつコスト抑制

**DynamoDB:**
- PAY_PER_REQUESTで使用量ベースの課金
- 月1回の一括書き込みのため固定容量より安価

## 災害復旧 (DR)

### バックアップ戦略

**DynamoDB:**
- Point-in-Time Recovery (PITR) の有効化を推奨
- オンデマンドバックアップの定期実行

**Lambda:**
- コードはGitリポジトリで管理
- CDKでいつでも再デプロイ可能

### リカバリ手順

1. スタック削除が必要な場合
   - prod環境: DynamoDBテーブルは保持される
   - dev環境: テーブルも削除される

2. データ復旧
   - DynamoDBバックアップから復元
   - または、Lambda関数を手動実行して再取得
