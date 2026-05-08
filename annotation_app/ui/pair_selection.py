"""Step 0: ペア選択画面."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import streamlit as st

from annotation_app.schemas.annotation import ItemAnnotation, PairAnnotation
from annotation_app.schemas.manifest import PairManifest
from annotation_app.storage.revision import next_revision
from annotation_app.storage.s3 import S3Storage


_JST = timezone(timedelta(hours=9), name="JST")


def render() -> None:
    st.title("1. ペア選択")
    st.markdown(
        "**作業の流れ:**  \n"
        "1. Worker ID とアノテーション対象のペア ID を入力してください。  \n"
        "2. 「開始」を押すと、既存のアノテーションがあれば再開、なければ新規作成します。"
    )
    st.divider()

    # マニフェストはフォーム外で事前取得
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

    with st.form("pair_select_form"):
        worker_id: str = st.text_input(
            "Worker ID",
            value=st.session_state.get("worker_id", os.environ.get("WORKER_ID", "")),
            placeholder="例: cw_001",
        )
        pair_id_input: str = st.text_input(
            "ペア ID",
            value=st.session_state.get("last_pair_id", ""),
            placeholder="例: いち__しち",
            help="アノテーションするペアの ID を直接入力してください。",
        )
        submitted = st.form_submit_button("開始", type="primary")

    # ── Worker ID が入力されていれば実績サマリーを表示 ────────
    display_worker_id = st.session_state.get("worker_id", os.environ.get("WORKER_ID", ""))
    if display_worker_id:
        try:
            import pandas as pd
            storage = S3Storage()
            worker_anns = storage.list_worker_annotations(display_worker_id)
            total = len(manifests)
            done = sum(1 for a in worker_anns if a.status == "completed")
            st.info(
                f"**{display_worker_id}** 様の実績: "
                f"完了 **{done}** 件（全 {total} ペア中）"
            )
            if worker_anns:
                rows = [
                    {
                        "ペア ID": a.pair_id,
                        "状態": "完了" if a.status == "completed" else "下書き",
                        "有効性": ("有効" if a.pair_is_valid else "無効") if a.pair_is_valid is not None else "—",
                        "最終更新": a.updated_at.astimezone(_JST).strftime("%m/%d %H:%M"),
                    }
                    for a in worker_anns
                ]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        except Exception:
            pass

    # ── 開始済みの場合: 現在のペアをアナウンス ────────────────
    annotation = st.session_state.get("annotation")
    manifest_loaded: PairManifest | None = st.session_state.get("pair_manifest")
    if annotation is not None and manifest_loaded is not None:
        st.success(
            f"✅ **{manifest_loaded.word_a} / {manifest_loaded.word_b}** を開始しました。  \n"
            "上の **「2. 有効性チェック」** タブに進んでください。"
        )

    if not submitted:
        return

    if not worker_id:
        st.warning("Worker ID を入力してください。")
        return

    if not pair_id_input:
        st.warning("ペア ID を入力してください。")
        return

    manifest: PairManifest | None = pair_id_map.get(pair_id_input)
    if manifest is None:
        st.warning(f"ペア ID `{pair_id_input}` が見つかりません。({len(manifests)} 件中)")
        return

    st.session_state.worker_id = worker_id
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
        st.info(f"リビジョン {existing.revision} を再開します。")
    else:
        _start_new(worker_id, manifest)

    # 前のペアのウィジェット状態をクリアして新しい accent_kana が反映されるようにする
    for key in list(st.session_state.keys()):
        if key.startswith(("accent_", "natural_", "notes_")):
            del st.session_state[key]

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
