"""リビジョン番号管理: 次のリビジョン番号を決定する."""

from __future__ import annotations

import os
import re

import boto3
from botocore.exceptions import ClientError


def _get_bucket() -> str:
    bucket = os.environ.get("S3_BUCKET", "")
    if not bucket:
        raise RuntimeError("環境変数 S3_BUCKET が設定されていません")
    return bucket


def _get_prefix() -> str:
    return os.environ.get("S3_PREFIX", "").rstrip("/")


def next_revision(worker_id: str, pair_id: str) -> int:
    """指定 worker / pair の次のリビジョン番号を返す.

    既存のリビジョンファイルが存在しない場合は 1 を返す.
    """
    s3 = boto3.client("s3")
    bucket = _get_bucket()
    prefix = _get_prefix()

    worker_safe = worker_id.replace("/", "_").replace("\\", "_")
    pair_safe = pair_id.replace("/", "_").replace("\\", "_")
    list_prefix = f"annotations/worker_id={worker_safe}/pair_id={pair_safe}/"
    if prefix:
        list_prefix = f"{prefix}/{list_prefix}"

    try:
        response = s3.list_objects_v2(Bucket=bucket, Prefix=list_prefix)
    except ClientError:
        return 1

    objects = response.get("Contents", [])
    if not objects:
        return 1

    revisions: list[int] = []
    for obj in objects:
        m = re.search(r"rev=(\d+)\.json$", obj["Key"])
        if m:
            revisions.append(int(m.group(1)))

    return max(revisions) + 1 if revisions else 1
