"""中間アノテーションを pair_manifest.jsonl に反映する処理."""

from __future__ import annotations

import json
from pathlib import Path

from annotation_app.schemas.annotation import PairAnnotation
from annotation_app.schemas.manifest import PairManifest


def load_manifest_jsonl(path: str | Path) -> list[PairManifest]:
    records: list[PairManifest] = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(PairManifest.model_validate(json.loads(line)))
    return records


def write_manifest_jsonl(path: str | Path, manifests: list[PairManifest]) -> None:
    with Path(path).open("w", encoding="utf-8") as f:
        for manifest in manifests:
            f.write(
                json.dumps(
                    manifest.model_dump(mode="json", exclude_none=True),
                    ensure_ascii=False,
                )
            )
            f.write("\n")


def merge_manifests_with_annotations(
    manifests: list[PairManifest],
    annotations: list[PairAnnotation],
) -> list[PairManifest]:
    """completed かつ valid な annotation を manifest に反映する.

    マージキーは item_id 単独ではなく (pair_id, item_id) の組を使う。
    item_id は pair_manifest をまたいで重複しうるため、pair_id を含めて対応付ける。
    """
    mergeable_annotations = [
        annotation
        for annotation in annotations
        if annotation.status == "completed" and annotation.pair_is_valid is True
    ]
    # item_id はペア間で重複するため、pair_id と組で index する。
    item_index = {
        (annotation.pair_id, item.item_id): item
        for annotation in mergeable_annotations
        for item in annotation.items
    }

    merged: list[PairManifest] = []
    for manifest in manifests:
        updated_items = []
        for item in manifest.items:
            annotated_item = item_index.get((manifest.pair_id, item.item_id))
            if annotated_item is None:
                updated_items.append(item)
                continue

            updated_items.append(
                item.model_copy(
                    update={
                        "corrected_kana": annotated_item.accent_kana,
                        "corrected": annotated_item.accent_kana != item.openjtalk_kana,
                        "is_natural_sentence": annotated_item.is_natural_sentence,
                    }
                )
            )

        merged.append(manifest.model_copy(update={"items": updated_items}))

    return merged