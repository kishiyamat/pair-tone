"""prosody_kana + prosody_pattern を Amazon Polly 用 SSML に変換する."""

from __future__ import annotations

import re
from xml.sax.saxutils import escape

from annotation_app.validation.mora import split_morae

_SPLIT_RE = re.compile(r"([/、])")

# 境界記号ごとのポーズ長
_PAUSE_MS: dict[str, str] = {
    "/": "200ms",
    "、": "500ms",
}


def phrase_to_accent_kana(kana_phrase: str, pattern_phrase: str) -> str:
    """L/H パターンからアクセント核マーカー ' を付与したカナを生成する.

    例:
        kana_phrase   = "メジロダイニ"
        pattern_phrase = "LHHLLL"
        -> "メジロ'ダイニ"   (H→L の直後に ' を挿入)
    """
    morae = split_morae(kana_phrase)
    result: list[str] = []
    for i, mora in enumerate(morae):
        result.append(mora)
        # 現在モーラが H で次モーラが L → アクセント核
        if i < len(pattern_phrase) - 1:
            if pattern_phrase[i] == "H" and pattern_phrase[i + 1] == "L":
                result.append("'")
    return "".join(result)


def _phrase_to_ssml_fragment(kana_phrase: str, pattern_phrase: str) -> str:
    """1フレーズ分の <phoneme> SSML フラグメントを生成する."""
    accent_kana = phrase_to_accent_kana(kana_phrase, pattern_phrase)
    ph_attr = escape(accent_kana)
    text = escape(kana_phrase)
    return f'<phoneme alphabet="x-amazon-pron-kana" ph="{ph_attr}">{text}</phoneme>'


def prosody_to_ssml(prosody_kana: str, prosody_pattern: str) -> str:
    """prosody_kana と prosody_pattern を Polly 用 SSML 文書に変換する.

    境界記号:
    - ``/``  → 短ポーズ (200ms)
    - ``、`` → 長ポーズ (500ms)

    Returns:
        ``<speak>`` で囲まれた SSML 文字列
    """
    kana_parts = _SPLIT_RE.split(prosody_kana)
    pat_parts = _SPLIT_RE.split(prosody_pattern)

    kana_phrases: list[str] = kana_parts[0::2]
    separators: list[str] = kana_parts[1::2]
    pat_phrases: list[str] = pat_parts[0::2]

    fragments: list[str] = []
    for i, (kp, pp) in enumerate(zip(kana_phrases, pat_phrases)):
        fragments.append(_phrase_to_ssml_fragment(kp, pp))
        if i < len(separators):
            pause_ms = _PAUSE_MS.get(separators[i], "200ms")
            fragments.append(f'<break time="{pause_ms}"/>')

    inner = "".join(fragments)
    return f'<speak><lang xml:lang="ja-JP">{inner}</lang></speak>'
