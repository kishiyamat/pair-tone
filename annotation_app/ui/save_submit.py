"""Step 3: 保存・提出画面."""

from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from annotation_app.schemas.annotation import PairAnnotation
from annotation_app.storage.s3 import S3Storage


def render() -> None:
    annotation: PairAnnotation | None = st.session_state.get("annotation")
    if annotation is None:
        st.error("アノテーションが見つかりません。")
        return

    st.title("3. 保存・提出")
    st.subheader(f"ペア: {annotation.pair_id}")

    # サマリー表示
    validity_label = "✓ 有効" if annotation.pair_is_valid else "✗ 無効"
    st.markdown(f"**有効性**: {validity_label}")
    if not annotation.pair_is_valid and annotation.pair_invalid_reason:
        st.markdown(f"**無効理由**: {annotation.pair_invalid_reason}")

    if annotation.pair_is_valid:
        done_count = sum(
            1 for it in annotation.items if it.prosody_kana and it.prosody_pattern
        )
        st.markdown(f"**編集済み**: {done_count} / {len(annotation.items)} 文")

    st.divider()

    col_back, col_draft, col_submit = st.columns([1, 1, 4])
    with col_back:
        if st.button("戻る"):
            st.session_state.step = "prosody" if annotation.pair_is_valid else "validity"
            st.rerun()
    with col_draft:
        if st.button("下書き保存"):
            _save(annotation, submit=False)
    with col_submit:
        if st.button("提出する", type="primary"):
            _save(annotation, submit=True)


def _save(annotation: PairAnnotation, *, submit: bool) -> None:
    now = datetime.now(timezone.utc)
    started: datetime = st.session_state.get("started_at", annotation.started_at)
    annotation.updated_at = now
    annotation.elapsed_sec = int((now - started).total_seconds())

    if submit:
        annotation.status = "completed"
        annotation.submitted_at = now
    else:
        annotation.status = "draft"

    st.session_state.annotation = annotation

    with st.spinner("S3 に保存中..."):
        try:
            storage = S3Storage()
            key = storage.save_annotation(annotation)
            if submit:
                storage.write_latest(annotation)
            if submit:
                st.success(f"提出が完了しました。(`{key}`)")
                st.balloons()
            else:
                st.success(f"下書きを保存しました。(`{key}`)")
        except Exception as e:
            st.error(f"保存に失敗しました: {e}")
