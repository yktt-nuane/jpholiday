# 開発ガイド

## 前提条件

### 必須ツール

1. **AWS CLI**
   ```bash
   aws --version  # AWS CLI 2.x 推奨
   aws configure  # AWSクレデンシャル設定
   ```

2. **AWS CDK CLI**
   ```bash
   npm install -g aws-cdk
   cdk --version  # 2.x系を使用
   ```

3. **Python**
   ```bash
   python3 --version  # Python 3.12以上
   ```

4. **Node.js & npm**
   ```bash
   node --version  # v14以上推奨
   npm --version
   ```

5. **Git**
   ```bash
   git --version
   ```

## 初期セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd jpholiday
```

### 2. 環境変数の設定

```bash
# .env.exampleをコピー
cp .env.example .env

# .envを編集して必要な値を設定
vi .env
```

必要な環境変数:
```bash
DYNAMODB_TABLE_NAME=jpholiday-table
LAMBDA_MEMORY_SIZE=128
LAMBDA_TIMEOUT=30
STAGE=dev  # または prod
JPHOLIDAY_LAYER_ARN=arn:aws:lambda:REGION:ACCOUNT:layer:jpholiday:VERSION
AWS_ACCOUNT=123456789012
AWS_REGION=ap-northeast-1
```

### 3. Python依存関係のインストール

```bash
# 本番依存関係
pip install -r requirements.txt

# 開発依存関係
pip install -r requirements-dev.txt
```

### 4. Node.js依存関係のインストール

```bash
npm install
```

### 5. Pre-commitフックの設定

```bash
npx husky install
```

## Lambda Layerの作成

jpholidayライブラリを含むLambda Layerを作成する必要があります。

### 方法1: Docker使用（推奨）

```bash
# ディレクトリ作成
mkdir -p lambda-layer/python

# Dockerコンテナ内でインストール
docker run --rm -v $(pwd)/lambda-layer:/var/task public.ecr.aws/lambda/python:3.9 \
    pip install jpholiday -t /var/task/python

# ZIPファイル作成
cd lambda-layer
zip -r jpholiday-layer.zip python
cd ..

# AWS Lambdaにレイヤーをアップロード
aws lambda publish-layer-version \
    --layer-name jpholiday \
    --zip-file fileb://lambda-layer/jpholiday-layer.zip \
    --compatible-runtimes python3.9 \
    --region ap-northeast-1

# 出力されたLayerVersionArnを.envのJPHOLIDAY_LAYER_ARNに設定
```

### 方法2: ローカルインストール

```bash
mkdir -p lambda-layer/python
pip install jpholiday boto3 aws-lambda-powertools -t lambda-layer/python
cd lambda-layer
zip -r jpholiday-layer.zip python
cd ..

# レイヤーをアップロード
aws lambda publish-layer-version \
    --layer-name jpholiday \
    --zip-file fileb://lambda-layer/jpholiday-layer.zip \
    --compatible-runtimes python3.12 \
    --region ap-northeast-1
```

## CDK Bootstrap

初回のみ、AWS環境でCDKをブートストラップする必要があります。

```bash
cdk bootstrap aws://ACCOUNT-NUMBER/REGION
```

例:
```bash
cdk bootstrap aws://123456789012/ap-northeast-1
```

## 開発ワークフロー

### コードの変更

1. **新しいブランチを作成**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **コードを編集**
   - CDKスタック: `jpholiday/jpholiday_stack.py`
   - Lambda関数: `lambda/index.py`
   - テスト: `tests/unit/test_jpholiday_stack.py`

3. **コードフォーマット**
   ```bash
   npm run format
   ```

   実行内容:
   - Black: コードフォーマット
   - isort: import文の整理
   - Ruff: リンターエラーの自動修正

4. **コード品質チェック**
   ```bash
   npm run lint
   ```

   実行内容:
   - Ruff: リンティング
   - mypy: 型チェック

5. **テスト実行**
   ```bash
   npm run test
   # または
   pytest
   pytest --cov  # カバレッジ付き
   ```

### Pre-commitフック

コミット時に自動実行される内容:
```bash
# .husky/pre-commitの内容
npm run format  # コードフォーマット
npm run lint    # 品質チェック
npm run test    # テスト実行
```

すべて成功するとコミットが完了します。失敗した場合はエラーを修正してください。

### CDK操作

#### スタック一覧の確認
```bash
cdk ls
```

#### CloudFormationテンプレート生成
```bash
cdk synth
```
生成されたテンプレートは`cdk.out/`ディレクトリに保存されます。

#### 変更差分の確認
```bash
cdk diff
```
現在のAWSリソースと比較して、デプロイ時の変更内容を表示します。

#### デプロイ
```bash
cdk deploy
```
CloudFormationスタックとしてAWSにデプロイします。

#### スタックの削除
```bash
cdk destroy
```
dev環境ではDynamoDBテーブルも削除されます。
prod環境ではテーブルは保持されます。

### Lambda関数のテスト

#### ローカルテスト

```bash
cd lambda
python3 << EOF
from index import handler
import json

# モックイベント
event = {}
context = None

# ローカル実行（要: boto3設定と環境変数）
result = handler(event, context)
print(json.dumps(result, indent=2, ensure_ascii=False))
EOF
```

#### AWS上でのテスト

```bash
# Lambda関数を手動実行
aws lambda invoke \
    --function-name JpHolidayStack-JpHolidayFunction... \
    --payload '{}' \
    response.json

# 結果確認
cat response.json
```

#### CloudWatch Logsの確認

```bash
# ロググループ確認
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/JpHolidayStack

# 最新ログストリーム確認
aws logs describe-log-streams \
    --log-group-name /aws/lambda/JpHolidayStack-JpHolidayFunction... \
    --order-by LastEventTime \
    --descending \
    --max-items 1

# ログ内容確認
aws logs tail /aws/lambda/JpHolidayStack-JpHolidayFunction... --follow
```

## テスト

### ユニットテスト

```bash
# すべてのテストを実行
pytest

# 詳細出力
pytest -v

# カバレッジレポート
pytest --cov

# 特定のテストファイルのみ
pytest tests/unit/test_jpholiday_stack.py

# 特定のテストケースのみ
pytest tests/unit/test_jpholiday_stack.py::test_dynamodb_table_created
```

### テストケース一覧

現在のテスト (tests/unit/test_jpholiday_stack.py):
- `test_dynamodb_table_created`: DynamoDBテーブルの作成確認
- `test_lambda_function_created`: Lambda関数の作成確認
- `test_eventbridge_rule_created`: EventBridgeルールの作成確認
- `test_dynamodb_removal_policy`: 環境別削除ポリシー確認
- `test_missing_environment_variables`: 環境変数バリデーション確認

## トラブルシューティング

### CDKデプロイエラー

**問題:** `cdk deploy`が失敗する

**解決策:**
```bash
# 1. Bootstrapの確認
cdk bootstrap

# 2. 認証情報の確認
aws sts get-caller-identity

# 3. 環境変数の確認
cat .env

# 4. CloudFormationスタックの状態確認
aws cloudformation describe-stacks --stack-name JpHolidayStack
```

### Lambda Layer エラー

**問題:** Lambda実行時に`jpholiday`モジュールが見つからない

**解決策:**
```bash
# 1. Layer ARNの確認
aws lambda list-layer-versions --layer-name jpholiday

# 2. .envのJPHOLIDAY_LAYER_ARNを最新バージョンに更新

# 3. 再デプロイ
cdk deploy
```

### DynamoDB 権限エラー

**問題:** Lambda実行時にDynamoDBへの書き込みが失敗

**解決策:**
```bash
# 1. Lambda実行ロールの確認
aws iam get-role --role-name JpHolidayStack-JpHolidayFunctionServiceRole...

# 2. ポリシーの確認
aws iam list-attached-role-policies --role-name JpHolidayStack-JpHolidayFunctionServiceRole...

# 3. CDKスタックの修正とデプロイ
cdk deploy
```

### Pre-commit フックエラー

**問題:** コミット時にフックがエラーを出す

**解決策:**
```bash
# 1. 手動でチェックを実行
npm run format
npm run lint
npm run test

# 2. エラーを修正

# 3. 再度コミット
git add .
git commit -m "your message"
```

**一時的にフックをスキップ:**
```bash
git commit -m "your message" --no-verify
```
※ただし、通常は推奨されません

## コードスタイルガイド

### Python (pyproject.toml)

- **フォーマッタ:** Black
  - 行の長さ: 100文字
  - ターゲット: Python 3.9

- **import整理:** isort
  - プロファイル: black互換

- **リンター:** Ruff
  - 除外: lambda/, cdk.out/

- **型チェック:** mypy
  - 厳密度: 緩め（段階的導入向け）

### コーディング規約

```python
# Good: 型ヒント付き
def handler(event: dict, context: Any) -> dict:
    """Lambda handler function."""
    pass

# Good: docstring
class JpHolidayStack(Stack):
    """CDK stack for JPHoliday application."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        """Initialize the stack."""
        super().__init__(scope, construct_id, **kwargs)

# Good: 環境変数のバリデーション
required_vars = ["VAR1", "VAR2"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing environment variables: {missing_vars}")
```

## リリースフロー

1. **開発ブランチで作業**
   ```bash
   git checkout -b feature/new-feature
   # 開発・テスト
   git commit -m "feat: add new feature"
   ```

2. **プルリクエスト作成**
   - GitHubでPRを作成
   - レビュー依頼

3. **レビュー後マージ**
   ```bash
   git checkout main
   git pull origin main
   ```

4. **本番デプロイ**
   ```bash
   # .envをprod環境に変更
   STAGE=prod cdk deploy
   ```

## 便利なコマンド集

```bash
# AWS関連
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `JpHoliday`)].FunctionName'
aws dynamodb list-tables --query 'TableNames[?contains(@, `jpholiday`)]'
aws logs tail /aws/lambda/<function-name> --follow --format short

# CDK関連
cdk synth --output cdk.out.json  # JSON形式で出力
cdk metadata  # スタックのメタデータ表示
cdk doctor    # CDK環境の診断

# Python関連
python -m pytest --collect-only  # テスト一覧表示
python -m black --check .        # フォーマット差分確認
python -m mypy . --show-error-codes  # 型エラー詳細

# Git関連
git log --oneline -10            # 最近のコミット10件
git diff main...feature/branch   # ブランチ間の差分
```

## 参考リンク

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [AWS Lambda Python Runtime](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)
- [jpholiday Documentation](https://pypi.org/project/jpholiday/)
- [pytest Documentation](https://docs.pytest.org/)
