"""Step 2: プロソディ編集画面."""

from __future__ import annotations

import streamlit as st

from annotation_app.schemas.annotation import ItemAnnotation, PairAnnotation
from annotation_app.schemas.manifest import ManifestItem, PairManifest
from annotation_app.ui.preview import render_preview_button
from annotation_app.validation.boundary import validate_boundary_layout


def render() -> None:
    st.title("2. プロソディ編集")

    manifest: PairManifest | None = st.session_state.get("pair_manifest")
    annotation: PairAnnotation | None = st.session_state.get("annotation")

    if manifest is None or annotation is None:
        st.error("ペアが選択されていません。")
        return

    st.subheader(f"ペア: {manifest.pair_id}")
    st.markdown(
        "各文の **prosody_kana** と **prosody_pattern** を編集してください。  \n"
        "- `prosody_kana`: 読み・フレーズ境界（`/`・`、`）・無声化（`_`）  \n"
        "- `prosody_pattern`: 各モーラを `L` / `H` で記述。境界は kana と揃える"
    )
    st.divider()

    # マニフェストアイテムを item_id で引けるようにする
    manifest_map: dict[int, ManifestItem] = {it.item_id: it for it in manifest.items}

    updated_items: list[ItemAnnotation] = []
    all_valid = True

    for idx, item_ann in enumerate(annotation.items):
        m_item = manifest_map.get(item_ann.item_id)
        ojt_kana = m_item.openjtalk_kana if m_item else "?"

        label = f"[{item_ann.condition_id}] {item_ann.target_word} — {item_ann.sentence[:30]}…"
        with st.expander(label, expanded=True):
            st.markdown(f"**文**: {item_ann.sentence}")
            st.caption(f"OpenJTalk: `{ojt_kana}`")

            col_kana, col_pat = st.columns(2)
            with col_kana:
                prosody_kana: str = st.text_input(
                    "prosody_kana",
                    value=item_ann.prosody_kana,
                    key=f"kana_{idx}",
                    placeholder="例: シュウマツニ/メジロダイニ/デカケタ",
                )
            with col_pat:
                prosody_pattern: str = st.text_input(
                    "prosody_pattern",
                    value=item_ann.prosody_pattern,
                    key=f"pat_{idx}",
                    placeholder="例: LHHHH/LHHLLL/LHHH",
                )

            # インライン検証
            if prosody_kana and prosody_pattern:
                errors = validate_boundary_layout(prosody_kana, prosody_pattern)
                if errors:
                    for err in errors:
                        st.warning(f"⚠ {err.message}")
                    all_valid = False
                else:
                    st.success("✓ OK")
            elif prosody_kana or prosody_pattern:
                st.info("両フィールドを入力してください。")
                all_valid = False

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

            preview_used = render_preview_button(
                prosody_kana,
                prosody_pattern,
                key_suffix=str(idx),
                already_used=item_ann.preview_used,
            )

        updated_items.append(
            ItemAnnotation(
                item_id=item_ann.item_id,
                condition_id=item_ann.condition_id,
                target_word=item_ann.target_word,
                sentence=item_ann.sentence,
                is_natural_sentence=is_natural,
                prosody_kana=prosody_kana,
                prosody_pattern=prosody_pattern,
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
        if st.button("保存・提出へ", type="primary", disabled=not all_valid):
            st.session_state.step = "submit"
            st.rerun()
