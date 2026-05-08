"""accent_kana を Amazon Polly 用 SSML に変換する."""

from __future__ import annotations

import re
from xml.sax.saxutils import escape

_CLAUSE_SEP_RE = re.compile(r"、")
_PHRASE_SEP_RE = re.compile(r"/")


def _phrase_to_ph(phrase: str) -> str:
    """ph 属性用: _ (無声化マーク) を除去、' はそのまま保持.

    / は呼び出し前に _PHRASE_SEP_RE で分割済みなので含まれない。
    x-amazon-pron-kana は 1 phoneme タグ = 1 アクセント句を前提とするため、
    / で分割して各フレーズを個別のタグにすることで ' を 1 つずつにする。
    """
    return phrase.replace("_", "")


def _phrase_to_text(phrase: str) -> str:
    """<phoneme> タグのテキストノード（Polly が ph 属性を無視した場合のフォールバック表示用）を生成する.

    アクセント情報は ph 属性に持たせるため、テキストノードには ' / _ を含めない。
    例: "ハナ'_シ" → "ハナシ"  （cf. ph 属性では "ハナ'シ"）
    """
    return phrase.replace("'", "").replace("\u2019", "").replace("_", "").replace("/", "")


def _clause_to_phonemes(clause: str) -> str:
    """1 つの、-節を phoneme タグ列に変換する.

    / で区切られた各アクセント句を個別の <phoneme> タグにする。
    Polly の x-amazon-pron-kana は 1 タグに ' が複数あると無視するため、
    必ず 1 フレーズ = 1 タグ = 1 アクセント核になるよう分割する。
    タグ間に空白を入れないことで余分なポーズを防ぐ。
    """
    phrases = _PHRASE_SEP_RE.split(clause)
    parts: list[str] = []
    for phrase in phrases:
        if not phrase.strip():
            continue
        ph = escape(_phrase_to_ph(phrase))
        text = escape(_phrase_to_text(phrase))
        parts.append(f'<phoneme alphabet="x-amazon-pron-kana" ph="{ph}">{text}</phoneme>')
    return "".join(parts)


def accent_kana_to_ssml(accent_kana: str) -> str:
    """accent_kana を Polly 用 SSML 文書に変換する.

    accent_kana 形式: "シュウマツニ'/メジロ'ダイニ/デカケタ'"
    - `'` アクセント核マーカー
    - `_` 無声化マーク（ph 属性では除去）
    - `/`  → アクセント句境界（フレーズごとに別 phoneme タグ、空白なし）
    - `、` → 節境界 + ポーズ (150ms)

    Returns:
        `<speak>` で囲まれた SSML 文字列
    """
    clauses = _CLAUSE_SEP_RE.split(accent_kana)

    fragments: list[str] = []
    for i, clause in enumerate(clauses):
        if clause.strip():
            fragments.append(_clause_to_phonemes(clause))
        if i < len(clauses) - 1:
            fragments.append('<break time="150ms"/>')

    inner = "".join(fragments)
    return f'<speak><lang xml:lang="ja-JP">{inner}</lang></speak>'
