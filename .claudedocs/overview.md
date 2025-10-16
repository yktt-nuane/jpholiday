# JPHoliday - Japanese Holiday Calendar AWS CDK

## プロジェクト概要

日本の祝日情報を自動的に取得し、Amazon DynamoDBに保存するサーバーレスアプリケーションです。AWS CDKを使用してインフラストラクチャをコードとして管理しています。

## 目的

- 日本の祝日データの自動管理
- スケーラブルで信頼性の高いサーバーレスアーキテクチャ
- 毎月自動実行により、常に最新の祝日情報を維持
- コスト効率の良い運用（月額約$0.30）

## 主な機能

1. **自動祝日取得**
   - 毎月1日 00:00 UTC に自動実行
   - 今後365日分の祝日を取得
   - jpholidayライブラリを使用

2. **データストレージ**
   - DynamoDBに祝日データを保存
   - PAY_PER_REQUEST課金モード
   - 環境別の削除ポリシー（dev/prod）

3. **Infrastructure as Code**
   - AWS CDKによる完全なインフラ定義
   - CloudFormationテンプレート自動生成
   - 環境変数ベースの設定管理

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| コンピュート | AWS Lambda (Python 3.12) |
| データベース | Amazon DynamoDB |
| スケジューリング | Amazon EventBridge |
| IaC | AWS CDK v2 |
| 外部ライブラリ | jpholiday, AWS Powertools |
| 依存関係管理 | boto3, aws-lambda-powertools |

## プロジェクト構成

```
jpholiday/
├── app.py                    # CDKアプリケーションエントリーポイント
├── jpholiday/               # CDKスタック定義
├── lambda/                  # Lambda関数コード
├── tests/                   # ユニットテスト
├── .claudedocs/            # Claudeドキュメント
└── requirements.txt        # 依存関係
```

## 月次コスト見積もり

- Lambda実行: 1回/月 × 5秒 = ほぼ無料
- DynamoDB: PAY_PER_REQUEST = 約$0.30/月
- EventBridge: 1イベント/月 = ほぼ無料

合計: 約$0.30/月

## 関連ドキュメント

- [アーキテクチャ詳細](./architecture.md)
- [開発ガイド](./development.md)
- [コードベース構造](./codebase.md)
