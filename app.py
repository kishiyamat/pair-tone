"""Pair Annotation App — Streamlit エントリポイント."""

from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Pair Annotation", layout="wide", page_icon="🎵")

# ── セッション状態の初期化 ──────────────────────────────────────
_DEFAULTS: dict[str, object] = {
    "manifests": [],
    "pair_manifest": None,
    "annotation": None,
    "worker_id": os.environ.get("WORKER_ID", ""),
    "started_at": None,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── サイドバー ────────────────────────────────────────────────
with st.sidebar:
    st.title("Pair Annotation")
    worker = st.session_state.get("worker_id") or "(未設定)"
    st.caption(f"Worker: {worker}")
    if st.session_state.pair_manifest is not None:
        st.caption(f"Pair: {st.session_state.pair_manifest.pair_id}")

# ── タブルーティング ──────────────────────────────────────────
from annotation_app.ui import (  # noqa: E402
    pair_selection,
    prosody_editor,
    save_submit,
    validity_check,
)

tab0, tab1, tab2, tab3 = st.tabs([
    "0. ペア選択",
    "1. 有効性チェック",
    "2. アクセント編集",
    "3. 保存・提出",
])

with tab0:
    pair_selection.render()

with tab1:
    validity_check.render()

with tab2:
    prosody_editor.render()

with tab3:
    save_submit.render()

