"""入力データスキーマ: ペアマニフェスト."""

from __future__ import annotations

from pydantic import BaseModel


class ManifestItem(BaseModel):
    """マニフェスト内の1アイテム（1文）."""

    item_id: int
    condition_id: str
    target_word: str
    sentence: str
    openjtalk_kana: str
    # 本番データに含まれる追加フィールド（省略可）
    foil_word: str | None = None
    bias_position: str | None = None
    bias_type: str | None = None
    target_slot: str | None = None
    corrected_kana: str | None = None
    corrected: bool | None = None
    is_natural_sentence: bool | None = None


class PairManifest(BaseModel):
    """1ペア分のマニフェスト（8アイテム）."""

    pair_id: str
    word_a: str
    word_b: str
    item_count: int | None = None
    items: list[ManifestItem]
