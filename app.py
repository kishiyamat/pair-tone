"""Pair Annotation App — Streamlit エントリポイント."""

from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Pair Annotation", layout="wide", page_icon="🎵")

# ── セッション状態の初期化 ──────────────────────────────────────
_DEFAULTS: dict[str, object] = {
    "step": "select",
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
    st.divider()

    _STEP_LABELS: dict[str, str] = {
        "select": "0. ペア選択",
        "validity": "1. 有効性チェック",
        "prosody": "2. プロソディ編集",
        "submit": "3. 保存・提出",
    }
    current_step: str = st.session_state.step
    for _step, _label in _STEP_LABELS.items():
        if _step == current_step:
            st.markdown(f"**→ {_label}**")
        else:
            st.markdown(f"　　{_label}")

# ── ステップルーティング ──────────────────────────────────────
from annotation_app.ui import (  # noqa: E402
    pair_selection,
    prosody_editor,
    save_submit,
    validity_check,
)

if current_step == "select":
    pair_selection.render()
elif current_step == "validity":
    validity_check.render()
elif current_step == "prosody":
    prosody_editor.render()
elif current_step == "submit":
    save_submit.render()
