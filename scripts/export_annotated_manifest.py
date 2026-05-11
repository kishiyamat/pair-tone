#!/usr/bin/env python3
"""S3 上の latest annotation を pair_manifest.jsonl に反映して書き出す."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from annotation_app.merge_jsonl import (
    load_manifest_jsonl,
    merge_manifests_with_annotations,
    write_manifest_jsonl,
)
from annotation_app.storage.s3 import S3Storage

load_dotenv()


def default_output_path(input_path: str) -> str:
    source = Path(input_path)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    if source.suffix:
        return str(source.with_name(f"{source.stem}.annotated.{timestamp}{source.suffix}"))
    return str(source.with_name(f"{source.name}.annotated.{timestamp}.jsonl"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="S3 の latest annotation を pair_manifest.jsonl に反映して書き出す"
    )
    parser.add_argument("input", help="元の pair_manifest.jsonl")
    parser.add_argument(
        "output",
        nargs="?",
        help="反映後の出力 JSONL パス。省略時は日時入りファイル名を自動生成する",
    )
    args = parser.parse_args()

    output_path = args.output or default_output_path(args.input)

    manifests = load_manifest_jsonl(args.input)
    annotations = S3Storage().list_latest_annotations()
    merged = merge_manifests_with_annotations(manifests, annotations)
    write_manifest_jsonl(output_path, merged)

    print(f"入力: {args.input}")
    print(f"出力: {output_path}")
    print(f"latest annotation 件数: {len(annotations)}")
    print(f"manifest 件数: {len(manifests)}")
    print("マージキー: pair_id + item_id")
    return 0


if __name__ == "__main__":
    sys.exit(main())