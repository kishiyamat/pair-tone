"""accent_kana を Amazon Polly 用 SSML に変換する."""

from __future__ import annotations

import re
from xml.sax.saxutils import escape

_SPLIT_RE = re.compile(r"([/、])")


def _phrase_to_ph(phrase: str) -> str:
    """ph 属性用文字列を生成する: _ (無声化マーク) を除去し ' はそのまま保持."""
    return phrase.replace("_", "")


def _phrase_to_text(phrase: str) -> str:
    """表示テキスト: ' と _ を除去したカナ."""
    return phrase.replace("'", "").replace("_", "")


def accent_kana_to_ssml(accent_kana: str) -> str:
    """accent_kana を Polly 用 SSML 文書に変換する.

    accent_kana 形式: "シュウマツニ'/メジロ'ダイニ/デカケタ'"
    - ``'`` アクセント核マーカー（Polly の x-amazon-pron-kana に直接渡す）
    - ``_`` 無声化マーク（ph 属性では除去）
    - ``/``  → アクセント句境界（ポーズなし、phoneme タグを隣接させるだけ）
    - ``、`` → 長ポーズ (500ms)

    Returns:
        ``<speak>`` で囲まれた SSML 文字列
    """
    parts = _SPLIT_RE.split(accent_kana)
    phrases: list[str] = parts[0::2]
    separators: list[str] = parts[1::2]

    fragments: list[str] = []
    for i, phrase in enumerate(phrases):
        if phrase:
            ph = escape(_phrase_to_ph(phrase))
            text = escape(_phrase_to_text(phrase))
            fragments.append(
                f'<phoneme alphabet="x-amazon-pron-kana" ph="{ph}">{text}</phoneme>'
            )
        if i < len(separators):
            sep = separators[i]
            if sep == "、":
                fragments.append('<break time="300ms"/>')
            # "/" はポーズなし: phoneme タグを並べるだけ

    inner = "".join(fragments)
    return f'<speak><lang xml:lang="ja-JP">{inner}</lang></speak>'
