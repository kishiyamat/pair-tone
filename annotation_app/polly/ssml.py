"""accent_kana を Amazon Polly 用 SSML に変換する."""

from __future__ import annotations

import re
from xml.sax.saxutils import escape

# 、のみで節を分割する。/ は accent phrase boundary だが Polly の ph 属性では不要なので除去する。
_CLAUSE_SEP_RE = re.compile(r"、")


def _phrase_to_ph(phrase: str) -> str:
    """ph 属性用: _ (無声化マーク) と / (アクセント句境界) を除去、' はそのまま保持.

    Polly の x-amazon-pron-kana は / を認識しないため、/ が残ると phoneme 要素全体が無視される。
    """
    return phrase.replace("_", "").replace("/", "")


def _phrase_to_text(phrase: str) -> str:
    """表示テキスト: ' / _ を除去したカナ."""
    return phrase.replace("’", "").replace("'", "").replace("_", "").replace("/", "")


def accent_kana_to_ssml(accent_kana: str) -> str:
    """accent_kana を Polly 用 SSML 文書に変換する.

    accent_kana 形式: "シュウマツニ'/メジロ'ダイニ/デカケタ'"
    - `'` アクセント核マーカー（Polly の x-amazon-pron-kana に直接渡す）
    - `_` 無声化マーク（ph 属性では除去）
    - `/`  → アクセント句境界（、で区切られた節内では 1 つの phoneme タグにまとめる）
    - `、` → 節境界 + ポーズ (150ms)

    Returns:
        `<speak>` で囲まれた SSML 文字列
    """
    clauses = _CLAUSE_SEP_RE.split(accent_kana)

    fragments: list[str] = []
    for i, clause in enumerate(clauses):
        if clause.strip():
            ph = escape(_phrase_to_ph(clause))
            text = escape(_phrase_to_text(clause))
            fragments.append(
                f'<phoneme alphabet="x-amazon-pron-kana" ph="{ph}">{text}</phoneme>'
            )
        if i < len(clauses) - 1:
            fragments.append('<break time="150ms"/>')

    inner = "".join(fragments)
    return f'<speak><lang xml:lang="ja-JP">{inner}</lang></speak>'
