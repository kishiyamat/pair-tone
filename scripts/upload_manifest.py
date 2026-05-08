#!/usr/bin/env python3
"""pair_manifest.jsonl を S3 の manifests/ にアップロードするスクリプト."""

from __future__ import annotations

import argparse
import os
import sys

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="pair_manifest.jsonl を S3 へアップロードする"
    )
    parser.add_argument("file", help="アップロードする JSONL ファイルのパス")
    parser.add_argument(
        "--dest",
        default="pair_manifest.jsonl",
        help="manifests/ 以下の保存先パス (例: retry01/pair_manifest.jsonl)",
    )
    args = parser.parse_args()

    bucket = os.environ.get("S3_BUCKET", "")
    if not bucket:
        print("Error: 環境変数 S3_BUCKET が設定されていません", file=sys.stderr)
        return 1

    prefix = os.environ.get("S3_PREFIX", "").rstrip("/")
    key = f"manifests/{args.dest}"
    if prefix:
        key = f"{prefix}/{key}"

    s3 = boto3.client("s3")
    print(f"アップロード: {args.file} -> s3://{bucket}/{key}")

    try:
        with open(args.file, "rb") as f:
            s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=f,
                ContentType="application/x-ndjson",
            )
        print("完了。")
        return 0
    except FileNotFoundError:
        print(f"Error: ファイルが見つかりません: {args.file}", file=sys.stderr)
        return 1
    except ClientError as e:
        print(f"Error: S3 エラー: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
