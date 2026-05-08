"""Step 1: ペア有効性チェック画面."""

from __future__ import annotations

import streamlit as st

from annotation_app.schemas.annotation import PairAnnotation
from annotation_app.schemas.manifest import PairManifest


def render() -> None:
    st.title("1. ペア有効性チェック")

    manifest: PairManifest | None = st.session_state.get("pair_manifest")
    annotation: PairAnnotation | None = st.session_state.get("annotation")

    if manifest is None or annotation is None:
        st.error("ペアが選択されていません。")
        if st.button("ペア選択に戻る"):
            st.session_state.step = "select"
            st.rerun()
        return

    st.subheader(f"ペア: {manifest.pair_id}")
    st.markdown(
        f"**ターゲット語 A**: {manifest.word_a}　"
        f"**ターゲット語 B**: {manifest.word_b}"
    )
    st.divider()
    st.markdown(
        "8 文すべてを確認し、このペアが有効な刺激セットかどうか判断してください。  \n"
        "（ターゲット語が同じ意味・用法で使われているかを確認）"
    )

    # 全 8 文を表示
    for item in manifest.items:
        with st.container(border=True):
            st.markdown(f"**[{item.condition_id}]** {item.target_word} — {item.sentence}")
            st.caption(f"OpenJTalk: `{item.openjtalk_kana}`")

    st.divider()

    # 有効/無効の選択
    default_index = 1 if annotation.pair_is_valid is False else 0
    is_valid_label: str = st.radio(  # type: ignore[assignment]
        "このペアは有効な刺激セットですか？",
        options=["有効", "無効"],
        index=default_index,
        horizontal=True,
    )

    invalid_reason = ""
    if is_valid_label == "無効":
        invalid_reason = st.text_area(
            "無効理由（必須）",
            value=annotation.pair_invalid_reason or "",
            placeholder="例: めじろ台は地名として使われているが、目白は鳥として使われている",
        )

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("戻る"):
            st.session_state.step = "select"
            st.rerun()
    with col2:
        next_label = "プロソディ編集へ" if is_valid_label == "有効" else "無効として提出画面へ"
        if st.button(next_label, type="primary"):
            if is_valid_label == "無効" and not invalid_reason.strip():
                st.error("無効の場合は理由を入力してください。")
                return

            annotation.pair_is_valid = is_valid_label == "有効"
            annotation.pair_invalid_reason = (
                invalid_reason.strip() if is_valid_label == "無効" else None
            )
            st.session_state.annotation = annotation
            st.session_state.step = "prosody" if annotation.pair_is_valid else "submit"
            st.rerun()
