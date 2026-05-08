"""出力データスキーマ: アノテーション記録."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ItemAnnotation(BaseModel):
    """1アイテム（1文）のアノテーション."""

    item_id: int
    condition_id: str
    target_word: str
    sentence: str
    is_natural_sentence: bool = True
    prosody_kana: str = ""
    prosody_pattern: str = ""
    preview_used: bool = False
    notes: str = ""


class PairAnnotation(BaseModel):
    """1ペア分のアノテーション記録（リビジョン単位で保存）."""

    pair_id: str
    worker_id: str
    revision: int
    status: Literal["draft", "completed"] = "draft"
    pair_is_valid: bool | None = None
    pair_invalid_reason: str | None = None
    started_at: datetime
    updated_at: datetime
    submitted_at: datetime | None = None
    elapsed_sec: int = 0
    items: list[ItemAnnotation] = Field(default_factory=list)
