"""Step 2: プロソディ編集画面."""

from __future__ import annotations

import streamlit as st

from annotation_app.schemas.annotation import ItemAnnotation, PairAnnotation
from annotation_app.schemas.manifest import ManifestItem, PairManifest
from annotation_app.ui.preview import render_audio


def render() -> None:
    st.title("2. アクセント編集")

    manifest: PairManifest | None = st.session_state.get("pair_manifest")
    annotation: PairAnnotation | None = st.session_state.get("annotation")

    if manifest is None or annotation is None:
        st.error("ペアが選択されていません。")
        return

    st.subheader(f"ペア: {manifest.pair_id}")
    st.markdown(
        "`'` をアクセント核の直後に置いてください（例: `メジロ'ダイニ/デカケタ'`）。  \n"
        "フレーズ区切りは `/`、ポーズは `、`、無声化は `_` を使います。"
    )
    st.divider()

    manifest_map: dict[int, ManifestItem] = {it.item_id: it for it in manifest.items}

    updated_items: list[ItemAnnotation] = []
    all_filled = True

    for idx, item_ann in enumerate(annotation.items):
        m_item = manifest_map.get(item_ann.item_id)
        label = f"[{item_ann.condition_id}] {item_ann.target_word} — {item_ann.sentence[:40]}…"

        with st.expander(label, expanded=True):
            st.markdown(f"**文:** {item_ann.sentence}")

            # 参照用: openjtalk_kana と corrected_kana を並べて表示
            if m_item:
                st.caption(f"OpenJTalk: `{m_item.openjtalk_kana}`")
                if (
                    m_item.corrected_kana
                    and m_item.corrected_kana != m_item.openjtalk_kana
                ):
                    st.caption(f"corrected:  `{m_item.corrected_kana}`")

            accent_kana: str = st.text_input(
                "accent_kana",
                value=item_ann.accent_kana,
                key=f"accent_{idx}",
                placeholder="例: シュウマツニ'/メジロ'ダイニ/デカケタ'",
            )

            if not accent_kana.strip():
                st.warning("入力してください。")
                all_filled = False

            col_check, col_notes = st.columns([1, 3])
            with col_check:
                is_natural: bool = st.checkbox(
                    "自然な文",
                    value=item_ann.is_natural_sentence,
                    key=f"natural_{idx}",
                )
            with col_notes:
                notes: str = st.text_input(
                    "メモ",
                    value=item_ann.notes,
                    key=f"notes_{idx}",
                )

            preview_used = render_audio(
                accent_kana=accent_kana,
                key_suffix=str(idx),
            )

        updated_items.append(
            ItemAnnotation(
                item_id=item_ann.item_id,
                condition_id=item_ann.condition_id,
                target_word=item_ann.target_word,
                sentence=item_ann.sentence,
                is_natural_sentence=is_natural,
                accent_kana=accent_kana,
                preview_used=preview_used,
                notes=notes,
            )
        )

    annotation.items = updated_items
    st.session_state.annotation = annotation

    st.divider()
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("戻る"):
            st.session_state.step = "validity"
            st.rerun()
    with col2:
        if st.button("保存・提出へ", type="primary", disabled=not all_filled):
            st.session_state.step = "submit"
            st.rerun()
