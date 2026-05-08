"""Polly 音声を自動取得してインライン再生するヘルパー.

accent_kana が変わった場合だけ再合成し、それ以外はキャッシュを使う。
ボタン操作は不要。
"""

from __future__ import annotations

import streamlit as st

from annotation_app.polly.client import PollyClient

# session_state のキー: "polly_cache" -> dict[key_suffix, (accent_kana, audio_bytes)]
_CACHE_KEY = "polly_cache"


def render_audio(
    accent_kana: str,
    key_suffix: str,
) -> bool:
    """accent_kana の音声を自動合成して st.audio で表示する.

    キャッシュ: accent_kana が前回と同じなら再合成しない。
    変わっていれば合成し直してキャッシュを更新する。

    Returns:
        音声が正常に表示されたかどうか（= preview_used 相当）
    """
    if _CACHE_KEY not in st.session_state:
        st.session_state[_CACHE_KEY] = {}

    cache: dict[str, tuple[str, bytes]] = st.session_state[_CACHE_KEY]

    if not accent_kana.strip():
        return False

    cached = cache.get(key_suffix)
    if cached is None or cached[0] != accent_kana:
        # 新規 or 変更あり → 再合成
        try:
            audio_bytes = PollyClient().synthesize(accent_kana)
        except Exception as e:
            st.error(f"音声合成失敗: {e}")
            return False
        cache[key_suffix] = (accent_kana, audio_bytes)

    _, audio_bytes = cache[key_suffix]
    st.audio(audio_bytes, format="audio/mp3")
    return True


# 後方互換エイリアス（他のコードが render_preview_button を呼んでいる場合用）
def render_preview_button(
    accent_kana: str,
    key_suffix: str,
    already_used: bool = False,
) -> bool:
    return render_audio(accent_kana, key_suffix)
