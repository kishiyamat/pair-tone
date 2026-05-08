"""Step 0: ペア選択画面."""

from __future__ import annotations

import os
from datetime import datetime, timezone

import streamlit as st

from annotation_app.schemas.annotation import ItemAnnotation, PairAnnotation
from annotation_app.schemas.manifest import PairManifest
from annotation_app.storage.revision import next_revision
from annotation_app.storage.s3 import S3Storage


def render() -> None:
    st.title("0. ペア選択")

    # Worker ID 入力
    worker_id: str = st.text_input(
        "Worker ID",
        value=st.session_state.get("worker_id", os.environ.get("WORKER_ID", "")),
        placeholder="例: cw_001",
    )
    st.session_state.worker_id = worker_id

    if not worker_id:
        st.warning("Worker ID を入力してください。")
        return

    # マニフェスト読み込み
    if st.button("S3 からマニフェストを読み込む"):
        with st.spinner("読み込み中..."):
            try:
                storage = S3Storage()
                manifests = storage.load_manifests()
                st.session_state.manifests = manifests
                st.success(f"{len(manifests)} 件のペアを読み込みました。")
            except Exception as e:
                st.error(f"読み込みに失敗しました: {e}")
                return

    manifests: list[PairManifest] = st.session_state.get("manifests", [])
    if not manifests:
        st.info("マニフェストを読み込んでください。")
        return

    pair_ids = [m.pair_id for m in manifests]
    selected_id: str | None = st.selectbox("ペアを選択", pair_ids)
    if selected_id is None:
        return

    manifest = next(m for m in manifests if m.pair_id == selected_id)

    with st.expander("ペア詳細"):
        st.json(
            {
                "pair_id": manifest.pair_id,
                "word_a": manifest.word_a,
                "word_b": manifest.word_b,
                "item_count": len(manifest.items),
            }
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("新規アノテーション開始", type="primary"):
            _start_new(worker_id, manifest)
    with col2:
        if st.button("最新リビジョンを再開"):
            _resume_latest(worker_id, manifest)


def _start_new(worker_id: str, manifest: PairManifest) -> None:
    try:
        rev = next_revision(worker_id, manifest.pair_id)
    except Exception:
        rev = 1

    now = datetime.now(timezone.utc)
    annotation = PairAnnotation(
        pair_id=manifest.pair_id,
        worker_id=worker_id,
        revision=rev,
        status="draft",
        started_at=now,
        updated_at=now,
        items=[
            ItemAnnotation(
                item_id=item.item_id,
                condition_id=item.condition_id,
                target_word=item.target_word,
                sentence=item.sentence,
                # OpenJTalk のアクセント核マーカー ' を除いた状態を初期値にする
                prosody_kana=item.openjtalk_kana.replace("'", ""),
                prosody_pattern="",
            )
            for item in manifest.items
        ],
    )
    st.session_state.pair_manifest = manifest
    st.session_state.annotation = annotation
    st.session_state.started_at = now
    st.session_state.step = "validity"
    st.rerun()


def _resume_latest(worker_id: str, manifest: PairManifest) -> None:
    try:
        storage = S3Storage()
        annotation = storage.load_latest_annotation(manifest.pair_id)
    except Exception as e:
        st.error(f"読み込みに失敗しました: {e}")
        return

    if annotation is None:
        st.warning("既存のアノテーションが見つかりません。新規開始してください。")
        return

    st.session_state.pair_manifest = manifest
    st.session_state.annotation = annotation
    st.session_state.worker_id = worker_id

    if annotation.pair_is_valid is None:
        st.session_state.step = "validity"
    elif annotation.pair_is_valid:
        st.session_state.step = "prosody"
    else:
        st.session_state.step = "submit"

    st.rerun()
