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
        st.info("「0. ペア選択」タブでペアを選択してください。")
        return

    st.subheader(f"ペア: {manifest.pair_id}")
    st.markdown(
        f"**ターゲット語 A**: {manifest.word_a}　"
        f"**ターゲット語 B**: {manifest.word_b}"
    )
    st.divider()
    st.markdown("8 文すべてを確認し、このペアが **有効な刺激セット** かどうか判断してください。")

    with st.expander("✅ 有効・無効の判断基準", expanded=False):
        st.markdown(
            """
**有効** とみなす条件（すべて満たすこと）

- ペアの両単語（A・B）が、それぞれの例文の中で **同じ意味・用法** で一貫して使われている
  - 例: 「めじろ台」がすべて地名として、「目白」がすべて地名として使われている → 有効
- 文が日本語として自然で、ターゲット語が文中で適切な役割を担っている

---

**無効** とみなす条件（一つでも該当すれば無効）

- 同一単語の例文間で **意味・用法がバラバラ**
  - 例: 「目白」の例文が鳥・地名・大学名などと混在している
- アルファベット略語・記号・固有名詞の英語表記など、**日本語プロソディ評価に不適切な語形**が含まれる
- 文の意味が不自然・不明瞭でターゲット語の用法が判断できない
- ターゲット語が文中で **全く意味的役割を果たしていない**（文脈から浮いている）
"""
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
            placeholder="例: 「目白」の例文で鳥と地名が混在している / アルファベット略語が含まれる",
        )

    col1, col2 = st.columns([1, 5])
    with col1:
        pass  # タブで自由に移動できるため「戻る」ボタンは不要
    with col2:
        next_label = "確定してアクセント編集へ" if is_valid_label == "有効" else "無効として確定"
        if st.button(next_label, type="primary"):
            if is_valid_label == "無効" and not invalid_reason.strip():
                st.error("無効の場合は理由を入力してください。")
                return

            annotation.pair_is_valid = is_valid_label == "有効"
            annotation.pair_invalid_reason = (
                invalid_reason.strip() if is_valid_label == "無効" else None
            )
            st.session_state.annotation = annotation
            st.info("確定しました。**「2. アクセント編集」**タブに進んでください。")
