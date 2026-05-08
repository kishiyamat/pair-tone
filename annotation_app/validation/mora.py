"""モーラ数カウントおよびカナ文字列の分割."""

from __future__ import annotations

import re

# 前のモーラに付属する小書きカナ（拗音・合拗音）
# ッ（促音）と ン（撥音）は独立モーラなので含めない
_SMALL_KANA: frozenset[str] = frozenset(
    "ァィゥェォャュョヮヵヶ"  # 小書きカタカナ
    "ぁぃぅぇぉゃゅょゎ"       # 小書きひらがな
)

# 境界記号
_BOUNDARY_RE = re.compile(r"[/、]")


def split_morae(kana: str) -> list[str]:
    """カナ文字列（境界記号なし）をモーラのリストに分割する.

    Rules:
    - 小書きカナ（ャ・ュ・ョ等）は直前のモーラに結合する
    - ``_`` （無声化マーク）はモーラとして数えない
    - ッ（促音）・ン（撥音）は独立モーラ
    """
    morae: list[str] = []
    for ch in kana:
        if ch == "_":
            continue
        if ch in _SMALL_KANA and morae:
            morae[-1] += ch
        else:
            morae.append(ch)
    return morae


def count_morae(kana: str) -> int:
    """カナ文字列（境界記号なし）のモーラ数を返す."""
    return len(split_morae(kana))


def strip_boundaries(text: str) -> str:
    """境界記号（/ と 、）を除去して返す."""
    return _BOUNDARY_RE.sub("", text)
