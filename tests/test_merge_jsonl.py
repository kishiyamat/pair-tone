from datetime import datetime, timezone

from annotation_app.merge_jsonl import merge_manifests_with_annotations
from annotation_app.schemas.annotation import ItemAnnotation, PairAnnotation
from annotation_app.schemas.manifest import ManifestItem, PairManifest


def _manifest() -> PairManifest:
    return PairManifest(
        pair_id="めじろ台__目白",
        word_a="めじろ台",
        word_b="目白",
        items=[
            ManifestItem(
                item_id=17,
                condition_id="a",
                target_word="めじろ台",
                sentence="週末にめじろ台に出かけた。",
                openjtalk_kana="シュウマツニ'/メジロ'ダイニ/デカケタ'",
            ),
            ManifestItem(
                item_id=18,
                condition_id="b",
                target_word="目白",
                sentence="週末に目白に出かけた。",
                openjtalk_kana="シュウマツニ'/メジロニ'/デカケタ'",
            ),
        ],
    )


def _annotation(*, status: str = "completed", pair_is_valid: bool | None = True) -> PairAnnotation:
    now = datetime.now(timezone.utc)
    return PairAnnotation(
        pair_id="めじろ台__目白",
        worker_id="cw_001",
        revision=1,
        status=status,
        pair_is_valid=pair_is_valid,
        started_at=now,
        updated_at=now,
        items=[
            ItemAnnotation(
                item_id=17,
                condition_id="a",
                target_word="めじろ台",
                sentence="週末にめじろ台に出かけた。",
                is_natural_sentence=True,
                accent_kana="シュウマツニ'/メジロ'ダイニ/デカケタ'",
            ),
            ItemAnnotation(
                item_id=18,
                condition_id="b",
                target_word="目白",
                sentence="週末に目白に出かけた。",
                is_natural_sentence=False,
                accent_kana="シュウマツニ'/メ'ジロニ/デカケタ'",
            ),
        ],
    )


class TestMergeManifestsWithAnnotations:
    def test_updates_completed_valid_annotations(self) -> None:
        merged = merge_manifests_with_annotations([_manifest()], [_annotation()])

        first_item = merged[0].items[0]
        second_item = merged[0].items[1]

        assert first_item.corrected_kana == "シュウマツニ'/メジロ'ダイニ/デカケタ'"
        assert first_item.corrected is False
        assert first_item.is_natural_sentence is True

        assert second_item.corrected_kana == "シュウマツニ'/メ'ジロニ/デカケタ'"
        assert second_item.corrected is True
        assert second_item.is_natural_sentence is False

    def test_ignores_draft_annotations(self) -> None:
        merged = merge_manifests_with_annotations([_manifest()], [_annotation(status="draft")])

        assert merged[0].items[1].corrected_kana is None
        assert merged[0].items[1].corrected is None

    def test_ignores_invalid_pair_annotations(self) -> None:
        merged = merge_manifests_with_annotations(
            [_manifest()],
            [_annotation(pair_is_valid=False)],
        )

        assert merged[0].items[1].corrected_kana is None
        assert merged[0].items[1].corrected is None