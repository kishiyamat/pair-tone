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

    st.subheader("保存・提出")
    st.subheader(f"ペア: {annotation.pair_id}")

    # サマリー表示
    validity_label = "✓ 有効" if annotation.pair_is_valid else "✗ 無効"
    st.markdown(f"**有効性**: {validity_label}")
    if not annotation.pair_is_valid and annotation.pair_invalid_reason:
        st.markdown(f"**無効理由**: {annotation.pair_invalid_reason}")

    if annotation.pair_is_valid:
        done_count = sum(
            1 for it in annotation.items if it.accent_kana
        )
        st.markdown(f"**編集済み**: {done_count} / {len(annotation.items)} 文")

    st.divider()

    if st.button("提出する", type="primary"):
        _save(annotation)

    # 保存結果メッセージ
    if msg := st.session_state.pop("_save_message", None):
        kind, text = msg
        if kind == "info":
            st.info(text)
        elif kind == "error":
            st.error(text)


def _save(annotation: PairAnnotation) -> None:
    now = datetime.now(timezone.utc)
    started: datetime = st.session_state.get("started_at", annotation.started_at)
    annotation.updated_at = now
    annotation.elapsed_sec = int((now - started).total_seconds())
    annotation.status = "completed"
    annotation.submitted_at = now

    st.session_state.annotation = annotation

    with st.spinner("S3 に保存中..."):
        try:
            storage = S3Storage()
            key = storage.save_annotation(annotation)
            storage.write_latest(annotation)
            st.session_state["_save_message"] = (
                "info",
                "提出が完了しました。"
                f"(`{key}`)\n\n"
                "次のタスクをお願いします。すべて完了した場合は、完了報告をお願いします。",
            )
            st.balloons()
        except Exception as e:
            st.session_state["_save_message"] = ("error", f"保存に失敗しました: {e}")
