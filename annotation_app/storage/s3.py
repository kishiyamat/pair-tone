"""S3 への読み書き操作."""

from __future__ import annotations

import json
import os

import boto3
import orjson
from botocore.exceptions import ClientError
from tenacity import retry, stop_after_attempt, wait_exponential

from annotation_app.schemas.annotation import PairAnnotation
from annotation_app.schemas.manifest import PairManifest


def _get_bucket() -> str:
    bucket = os.environ.get("S3_BUCKET", "")
    if not bucket:
        raise RuntimeError("環境変数 S3_BUCKET が設定されていません")
    return bucket


def _get_prefix() -> str:
    return os.environ.get("S3_PREFIX", "").rstrip("/")


class S3Storage:
    """マニフェストとアノテーションを S3 で管理するストレージクラス."""

    def __init__(self) -> None:
        self._s3 = boto3.client("s3")
        self._bucket = _get_bucket()
        self._prefix = _get_prefix()

    def _key(self, path: str) -> str:
        if self._prefix:
            return f"{self._prefix}/{path}"
        return path

    @staticmethod
    def _safe_id(text: str) -> str:
        """S3 キーとして安全な文字列に変換する."""
        return text.replace("/", "_").replace("\\", "_")

    # ── マニフェスト ────────────────────────────────────────────

    def _list_manifest_keys(self) -> list[str]:
        """manifests/ 配下の全 .jsonl キーを列挙する."""
        list_prefix = self._key("manifests/")
        keys: list[str] = []
        paginator = self._s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self._bucket, Prefix=list_prefix):
            for obj in page.get("Contents", []):
                key: str = obj["Key"]
                if key.endswith(".jsonl"):
                    keys.append(key)
        return sorted(keys)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4))
    def _load_jsonl(self, key: str) -> list[PairManifest]:
        """S3 上の JSONL ファイルを読み込んで PairManifest のリストを返す."""
        obj = self._s3.get_object(Bucket=self._bucket, Key=key)
        body: str = obj["Body"].read().decode("utf-8")
        records = [json.loads(line) for line in body.splitlines() if line.strip()]
        return [PairManifest.model_validate(r) for r in records]

    def load_manifests(self) -> list[PairManifest]:
        """manifests/ 配下の全 JSONL を読み込んで返す.

        pair_manifest.jsonl と retry01/pair_manifest.jsonl など
        複数ファイルが存在する場合もすべて結合して返す。
        pair_id が重複する場合は後から読んだものを優先する。
        """
        keys = self._list_manifest_keys()
        seen: dict[str, PairManifest] = {}
        for key in keys:
            for manifest in self._load_jsonl(key):
                seen[manifest.pair_id] = manifest
        return list(seen.values())

    # ── アノテーション保存 ───────────────────────────────────────

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4))
    def save_annotation(self, annotation: PairAnnotation) -> str:
        """アノテーションをリビジョンファイルとして保存する. 書き込んだ S3 キーを返す."""
        rev_str = f"{annotation.revision:04d}"
        worker_safe = self._safe_id(annotation.worker_id)
        pair_safe = self._safe_id(annotation.pair_id)
        key = self._key(
            f"annotations/worker_id={worker_safe}/pair_id={pair_safe}/rev={rev_str}.json"
        )
        body = orjson.dumps(
            annotation.model_dump(mode="json"),
            option=orjson.OPT_INDENT_2,
        )
        self._s3.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=body,
            ContentType="application/json",
        )
        return key

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4))
    def write_latest(self, annotation: PairAnnotation) -> str:
        """latest/ に最新スナップショットを書き込む. S3 キーを返す."""
        pair_safe = self._safe_id(annotation.pair_id)
        key = self._key(f"latest/pair_id={pair_safe}.json")
        body = orjson.dumps(
            annotation.model_dump(mode="json"),
            option=orjson.OPT_INDENT_2,
        )
        self._s3.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=body,
            ContentType="application/json",
        )
        return key

    # ── アノテーション読み込み ────────────────────────────────────

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4))
    def load_latest_annotation(self, pair_id: str) -> PairAnnotation | None:
        """latest/ から最新アノテーションを読み込む. なければ None."""
        pair_safe = self._safe_id(pair_id)
        key = self._key(f"latest/pair_id={pair_safe}.json")
        try:
            obj = self._s3.get_object(Bucket=self._bucket, Key=key)
            data = orjson.loads(obj["Body"].read())
            return PairAnnotation.model_validate(data)
        except ClientError as e:
            if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
                return None
            raise

    def list_worker_annotations(self, worker_id: str) -> list[PairAnnotation]:
        """指定ワーカーの全アノテーション（ペアごとの最新リビジョン）を返す.

        S3 パス: annotations/worker_id={worker_safe}/pair_id={pair_safe}/rev={rev}.json
        ペアごとに最大リビジョンのファイルを読み込む。
        updated_at 降順で返す。
        """
        worker_safe = self._safe_id(worker_id)
        prefix = self._key(f"annotations/worker_id={worker_safe}/")

        # pair_id フォルダ名 → 最新キー を収集（rev は zero-padded なので辞書順 = 数値順）
        pair_latest: dict[str, str] = {}
        paginator = self._s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key: str = obj["Key"]
                if not key.endswith(".json"):
                    continue
                parts = key.split("/")
                pair_part = next((p for p in parts if p.startswith("pair_id=")), None)
                if pair_part is None:
                    continue
                existing = pair_latest.get(pair_part)
                if existing is None or key > existing:
                    pair_latest[pair_part] = key

        results: list[PairAnnotation] = []
        for key in pair_latest.values():
            try:
                obj = self._s3.get_object(Bucket=self._bucket, Key=key)
                data = orjson.loads(obj["Body"].read())
                results.append(PairAnnotation.model_validate(data))
            except Exception:
                continue

        return sorted(results, key=lambda a: a.updated_at, reverse=True)
