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
    st.markdown(
        "**作業の流れ:**  \n"
        "1. Worker ID とアノテーション対象のペア ID を入力してください。  \n"
        "2. 「開始」を押すと、既存のアノテーションがあれば再開、なければ新規作成します。"
    )
    st.divider()

    # ── Worker ID ────────────────────────────────────────────
    worker_id: str = st.text_input(
        "Worker ID",
        value=st.session_state.get("worker_id", os.environ.get("WORKER_ID", "")),
        placeholder="例: cw_001",
    )
    st.session_state.worker_id = worker_id

    if not worker_id:
        st.warning("Worker ID を入力してください。")
        return

    # ── ペア ID 入力 ──────────────────────────────────────────
    pair_id_input: str = st.text_input(
        "ペア ID",
        value=st.session_state.get("last_pair_id", ""),
        placeholder="例: いち__しち",
        help="アノテーションするペアの ID を直接入力してください。",
    )

    # マニフェストがまだ読み込まれていなければバックグラウンドで取得
    if not st.session_state.get("manifests"):
        with st.spinner("S3 からマニフェストを読み込んでいます..."):
            try:
                storage = S3Storage()
                st.session_state.manifests = storage.load_manifests()
            except Exception as e:
                st.error(f"マニフェストの読み込みに失敗しました: {e}")
                return

    manifests: list[PairManifest] = st.session_state.manifests
    pair_id_map: dict[str, PairManifest] = {m.pair_id: m for m in manifests}

    # 入力値を検証
    manifest: PairManifest | None = None
    if pair_id_input:
        manifest = pair_id_map.get(pair_id_input)
        if manifest is None:
            st.warning(f"ペア ID `{pair_id_input}` が見つかりません。({len(manifests)} 件中)")
        else:
            st.success(
                f"✓ ペア確認: **{manifest.word_a}** / **{manifest.word_b}**"
                f"　({len(manifest.items)} 文)"
            )

    # ── 開始ボタン ───────────────────────────────────────────
    if st.button("開始", type="primary", disabled=manifest is None):
        assert manifest is not None
        st.session_state.last_pair_id = pair_id_input
        _start_or_resume(worker_id, manifest)


def _start_or_resume(worker_id: str, manifest: PairManifest) -> None:
    """既存アノテーションがあれば再開、なければ新規作成する."""
    with st.spinner("確認中..."):
        try:
            storage = S3Storage()
            existing = storage.load_latest_annotation(manifest.pair_id)
        except Exception as e:
            st.error(f"S3 の確認に失敗しました: {e}")
            return

    if existing is not None:
        st.session_state.pair_manifest = manifest
        st.session_state.annotation = existing
        st.session_state.worker_id = worker_id
        st.toast(f"リビジョン {existing.revision} を再開します。")
    else:
        _start_new(worker_id, manifest)

    st.rerun()


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
                # corrected_kana があればそれを、なければ openjtalk_kana から ' を除いた値を初期値にする
                accent_kana=(
                    item.corrected_kana
                    if item.corrected_kana
                    else item.openjtalk_kana
                ),
            )
            for item in manifest.items
        ],
    )
    st.session_state.pair_manifest = manifest
    st.session_state.annotation = annotation
    st.session_state.started_at = now
    st.rerun()
