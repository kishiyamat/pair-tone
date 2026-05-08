"""Polly プレビューボタンのレンダリングヘルパー."""

from __future__ import annotations

import streamlit as st

from annotation_app.polly.client import PollyClient


def render_preview_button(
    accent_kana: str,
    key_suffix: str,
    already_used: bool = False,
) -> bool:
    """Polly プレビューボタンを表示する. プレビューが使用済みかどうかを返す."""
    state_key = f"preview_used_{key_suffix}"
    if state_key not in st.session_state:
        st.session_state[state_key] = already_used

    if not accent_kana:
        return bool(st.session_state[state_key])

    if st.button("▶ Polly プレビュー", key=f"preview_btn_{key_suffix}"):
        with st.spinner("音声合成中..."):
            try:
                client = PollyClient()
                audio_bytes = client.synthesize(accent_kana)
                st.audio(audio_bytes, format="audio/mp3")
                st.session_state[state_key] = True
            except Exception as e:
                st.error(f"プレビュー失敗: {e}")

    return bool(st.session_state[state_key])
