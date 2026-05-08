"""prosody_kana と prosody_pattern の境界整合性を検証する."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from annotation_app.validation.mora import count_morae

_SPLIT_RE = re.compile(r"([/、])")
_VALID_PATTERN_CHARS = frozenset("LH")


@dataclass
class BoundaryError:
    """境界検証エラー."""

    message: str
    phrase_index: int | None = field(default=None)


def _split_with_separators(text: str) -> tuple[list[str], list[str]]:
    """/ と 、 で分割し、フレーズリストと区切り記号リストを返す."""
    parts = _SPLIT_RE.split(text)
    phrases: list[str] = parts[0::2]
    separators: list[str] = parts[1::2]
    return phrases, separators


def validate_boundary_layout(
    prosody_kana: str,
    prosody_pattern: str,
) -> list[BoundaryError]:
    """prosody_kana と prosody_pattern の境界整合性を検証する.

    チェック内容:
    1. 区切り記号の数が一致する
    2. 区切り記号の種類（/ vs 、）が同じ順序で並ぶ
    3. 各フレーズのモーラ数が一致する
    4. prosody_pattern が L / H のみで構成されている
    """
    errors: list[BoundaryError] = []

    kana_phrases, kana_seps = _split_with_separators(prosody_kana)
    pat_phrases, pat_seps = _split_with_separators(prosody_pattern)

    # 1. 区切り記号の数
    if len(kana_seps) != len(pat_seps):
        errors.append(
            BoundaryError(
                f"区切り記号の数が一致しません "
                f"(kana={len(kana_seps)}, pattern={len(pat_seps)})"
            )
        )
        return errors  # 以降のチェックは意味がない

    # 2. 区切り記号の種類
    for i, (ks, ps) in enumerate(zip(kana_seps, pat_seps)):
        if ks != ps:
            errors.append(
                BoundaryError(
                    f"区切り記号 {i + 1} 番目が一致しません: "
                    f"kana='{ks}', pattern='{ps}'"
                )
            )

    # 3 & 4. フレーズ単位の検証
    for i, (kp, pp) in enumerate(zip(kana_phrases, pat_phrases)):
        # パターンに無効な文字が含まれていないか
        invalid_chars = set(pp) - _VALID_PATTERN_CHARS
        if invalid_chars:
            errors.append(
                BoundaryError(
                    f"フレーズ {i + 1}: prosody_pattern に無効な文字が含まれています: "
                    f"{sorted(invalid_chars)}",
                    phrase_index=i,
                )
            )
            continue

        kana_count = count_morae(kp)
        pat_count = len(pp)
        if kana_count != pat_count:
            errors.append(
                BoundaryError(
                    f"フレーズ {i + 1}: モーラ数が一致しません "
                    f"(kana={kana_count}, pattern={pat_count})",
                    phrase_index=i,
                )
            )

    return errors
