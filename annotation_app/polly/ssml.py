"""accent_kana を Amazon Polly 用 SSML に変換する."""

from __future__ import annotations

import re
from xml.sax.saxutils import escape

_CLAUSE_SEP_RE = re.compile(r"、")
_PHRASE_SEP_RE = re.compile(r"/")

# フレーズ末尾の ' を検出する正規表現
# OpenJTalk では末尾 ' は 0型（平板型）の区切りマーカーであり、アクセント下降点ではない
_TRAILING_ACCENT_RE = re.compile(r"'$")


def _phrase_to_ph(phrase: str) -> str:
    """ph 属性用文字列を生成する.

    OpenJTalk の accent_kana フォーマットでは、アクセント句の末尾に付く '
    は「このフレーズにはアクセント下降がない（0型 / 平板型）」を意味する
    区切りマーカーである。Polly の x-amazon-pron-kana に末尾 ' を渡すと
    「最終モーラの後で下降せよ」と誤解釈されるため、除去する。

    一方、句の途中にある ' はアクセント核（下降開始点）を示すため保持する。

    例:
        "ハナ'シテ"     → "ハナ'シテ"   # 2モーラ目後下降 (2型)
        "エンシュツオ'" → "エンシュツオ" # 平板型、末尾 ' を除去
        "イタ'"         → "イタ"         # 平板型、末尾 ' を除去

    他にも除去する文字:
        _ (無声化マーク): Polly は認識しない
    """
    ph = phrase.replace("_", "")
    ph = _TRAILING_ACCENT_RE.sub("", ph)
    return ph


def _phrase_to_text(phrase: str) -> str:
    """<phoneme> タグのテキストノード（Polly が ph 属性を無視した場合のフォールバック表示用）を生成する.

    アクセント情報は ph 属性に持たせるため、テキストノードには ' / _ を含めない。
    例: "ハナ'_シ" → "ハナシ"  （cf. ph 属性では "ハナ'シ"）
    """
    return phrase.replace("'", "").replace("’", "").replace("_", "").replace("/", "")


# この閾値以上のフレーズが 「、」なしで連続すると不自然なポーズが入りやすい
_WARN_PHRASE_COUNT = 6


def _clause_to_phonemes(clause: str) -> str:
    """1 つの、-節を phoneme タグ列に変換する.

    / で区切られた各アクセント句を個別の <phoneme> タグにする。
    Polly の x-amazon-pron-kana は 1 タグに ' が複数あると無視するため、
    必ず 1 フレーズ = 1 タグ = 1 アクセント核になるよう分割する。
    """
    phrases = _PHRASE_SEP_RE.split(clause)
    parts: list[str] = []
    for phrase in phrases:
        if not phrase.strip():
            continue
        ph = escape(_phrase_to_ph(phrase))
        text = escape(_phrase_to_text(phrase))
        parts.append(
            f'<phoneme alphabet="x-amazon-pron-kana" ph="{ph}">{text}</phoneme>'
        )
    return "".join(parts)


def long_clause_warnings(accent_kana: str) -> list[str]:
    """フレーズ数が多い節を検出し、警告メッセージのリストを返す.

    「、」なしで _WARN_PHRASE_COUNT 以上の句が連続する節を検出し、
    中間付近への「、」挿入を促す警告を返す。
    """
    warnings: list[str] = []
    for clause in _CLAUSE_SEP_RE.split(accent_kana):
        phrases = [p for p in _PHRASE_SEP_RE.split(clause) if p.strip()]
        if len(phrases) >= _WARN_PHRASE_COUNT:
            warnings.append(
                f"「{clause}」に {len(phrases)} フレーズが連続しています。"
                " 不自然に聞こえる場合は「、」を追加してください。"
            )
    return warnings


def accent_kana_to_ssml(accent_kana: str) -> str:
    """accent_kana を Polly 用 SSML 文書に変換する.

    accent_kana フォーマット (OpenJTalk 準拠):
        サ'ッキマデ/ミナデ'/ア'_クションニ/ツ'イテ/ハナ'_シテ/イタ'

    記号の意味と変換ルール:

    | 記号 | 意味                                    | ph 属性での扱い           |
    |------|-----------------------------------------|---------------------------|
    | '    | アクセント核: 次のモーラから下降        | 保持                      |
    | '    | フレーズ末尾のみ: 0型（下降なし）マーカ | 除去                      |
    | _    | 無声化モーラ                            | 除去                      |
    | /    | アクセント句境界（ポーズなし）           | 別 <phoneme> タグに分割   |
    | 、   | 文節境界 + 100ms ポーズ                 | <break time="100ms"/> 挿入|

    末尾 ' の除去について:
        OpenJTalk では ' がフレーズの最終モーラの直後にある場合
        （例: "イタ'" "エンシュツオ'"）は 0型（平板型）を意味する。
        Polly の x-amazon-pron-kana に渡すと末尾下降と誤解釈されるため除去する。
        句中の ' （例: "ハナ'シテ"）はアクセント核を示すため保持する。

    Returns:
        `<speak>` で囲まれた SSML 文字列
    """
    clauses = _CLAUSE_SEP_RE.split(accent_kana)

    fragments: list[str] = []
    for i, clause in enumerate(clauses):
        if clause.strip():
            fragments.append(_clause_to_phonemes(clause))
        if i < len(clauses) - 1:
            fragments.append('<break time="100ms"/>')

    inner = "".join(fragments)
    return f'<speak><lang xml:lang="ja-JP">{inner}</lang></speak>'
