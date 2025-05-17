# 日本の祝日カレンダー AWS CDK

日本の祝日を自動的に取得し、Amazon DynamoDBに保存するサーバーレスアプリケーションです。このアプリケーションは毎月実行され、祝日データを常に最新の状態に保ちます。

## アーキテクチャ

![アーキテクチャ図](https://via.placeholder.com/800x400?text=アーキテクチャ図)

- **AWS Lambda**: 毎月1回実行され、今後の日本の祝日を取得します
- **Amazon DynamoDB**: 祝日情報を保存します
- **Amazon EventBridge**: 毎月1日にLambdaを実行するようにスケジュールします
- **AWS CDK**: すべてのコンポーネントをデプロイするためのインフラストラクチャコード

## 特徴

- 次の365日間の日本の祝日を自動的に取得します
- データベースを最新に保つために毎月実行されます
- AWS CDKで簡単にデプロイできます
- 環境変数で設定可能です

## 前提条件

- [AWSアカウント](https://aws.amazon.com/jp/account/)
- 適切な権限で設定された[AWS CLI](https://aws.amazon.com/jp/cli/)
- [Node.js](https://nodejs.org/) (≥ 14.x)
- [Python](https://www.python.org/) (≥ 3.9)
- グローバルにインストールされた[AWS CDK Toolkit](https://docs.aws.amazon.com/cdk/latest/guide/cli.html) (`npm install -g aws-cdk`)

## セットアップ

1. このリポジトリをクローンします:
   ```
   git clone https://github.com/yourusername/jp-holiday-calendar.git
   cd jp-holiday-calendar
   ```

2. 仮想環境を作成します:
   ```
   python -m venv .venv
   ```

3. 仮想環境を有効にします:
   - MacOS/Linuxの場合:
     ```
     source .venv/bin/activate
     ```
   - Windowsの場合:
     ```
     .venv\Scripts\activate.bat
     ```

4. 依存関係をインストールします:
   ```
   pip install -r requirements.txt
   ```

5. プロジェクトのルートに以下の変数を含む`.env`ファイルを作成します:
   ```
   DYNAMODB_TABLE_NAME=jp-holidays
   LAMBDA_MEMORY_SIZE=128
   LAMBDA_TIMEOUT=30
   STAGE=dev
   JPHOLIDAY_LAYER_ARN=arn:aws:lambda:YOUR_REGION:YOUR_ACCOUNT_ID:layer:jpholiday-layer:VERSION
   AWS_ACCOUNT=YOUR_ACCOUNT_ID
   AWS_REGION=YOUR_REGION
   ```

   注: jpholidayパッケージ用のLambdaレイヤーを作成するか、既存のものを使用する必要があります。

## jpholiday Lambda レイヤーの作成

jpholiday Lambdaレイヤーを作成するには:

1. 一時ディレクトリを作成します:
   ```
   mkdir -p /tmp/python
   ```

2. jpholidayをディレクトリにインストールします:
   ```
   pip install jpholiday -t /tmp/python
   ```

3. 内容をZIP化します:
   ```
   cd /tmp
   zip -r jpholiday-layer.zip python
   ```

4. AWS Lambdaでレイヤーを作成します:
   ```
   aws lambda publish-layer-version \
     --layer-name jpholiday-layer \
     --description "jpholiday library for Python" \
     --compatible-runtimes python3.9 \
     --zip-file fileb:///tmp/jpholiday-layer.zip
   ```

5. 出力からARNをメモし、`.env`ファイルを更新します。

## デプロイ

1. AWS環境をブートストラップします（まだ行っていない場合）:
   ```
   cdk bootstrap aws://YOUR_ACCOUNT_ID/YOUR_REGION
   ```

2. スタックをデプロイします:
   ```
   cdk deploy
   ```

## 動作の仕組み

1. Lambdaファンクションは毎月1日にトリガーされます
2. jpholidayライブラリを使用して、今後365日間の日本の祝日を取得します
3. 祝日は以下の構造でDynamoDBに保存されます:
   - `date` (パーティションキー): YYYY-MM-DD形式の祝日の日付
   - `name`: 祝日の名前（日本語）

## テスト

```
pytest
```

## 便利なコマンド

- `cdk ls` - アプリ内のすべてのスタックをリストアップします
- `cdk synth` - 合成されたCloudFormationテンプレートを出力します
- `cdk deploy` - このスタックをデフォルトのAWSアカウント/リージョンにデプロイします
- `cdk diff` - デプロイされたスタックと現在の状態を比較します
- `cdk docs` - CDKドキュメントを開きます

## クリーンアップ

このスタックによって作成されたすべてのリソースを削除するには:

```
cdk destroy
```

## ライセンス

[MIT](LICENSE)

## 貢献

貢献は歓迎します！お気軽にプルリクエストを提出してください。