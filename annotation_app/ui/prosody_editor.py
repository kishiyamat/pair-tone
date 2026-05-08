"""Step 2: プロソディ編集画面."""

from __future__ import annotations

import re

import streamlit as st

from annotation_app.schemas.annotation import ItemAnnotation, PairAnnotation
from annotation_app.schemas.manifest import ManifestItem, PairManifest
from annotation_app.ui.preview import render_audio

_PHRASE_SEP_RE = re.compile(r"[/、]")


def _validate_accent_kana(accent_kana: str) -> list[str]:
    """各フレーズに ' がちょうど 1 つあるか検証する. エラーメッセージのリストを返す."""
    if not accent_kana.strip():
        return []
    errors: list[str] = []
    for phrase in _PHRASE_SEP_RE.split(accent_kana):
        phrase = phrase.strip()
        if not phrase:
            continue
        count = phrase.count("'")
        if count == 0:
            errors.append(f"`{phrase}` にアクセント核 `'` がありません")
        elif count > 1:
            errors.append(f"`{phrase}` に `'` が {count} 個あります（1 個だけにしてください）")
    return errors


def render() -> None:
    st.title("3. アクセント編集")

    manifest: PairManifest | None = st.session_state.get("pair_manifest")
    annotation: PairAnnotation | None = st.session_state.get("annotation")

    if manifest is None or annotation is None:
        st.info("「1. ペア選択」タブでペアを選択してください。")
        return

    st.subheader(f"ペア: {manifest.pair_id}")

    with st.expander("📖 記法と編集のコツ", expanded=False):
        st.markdown(
            """
#### 記号一覧

| 記号 | 意味 | 例 |
|---|---|---|
| `'` | アクセント核（ピッチが下がる点）| `ハナ'ガ`（花が）、`ハナガ'`（鼻が） |
| `/` | アクセントフレーズ区切り（ポーズなし） | `メジロ'ダイニ/デカケタ'` |
| `、` | ポーズ付き区切り（`/` より長い間） | `ソ'レデワ、ツ'ギノ` |
| `_` | 母音の無声化 | `ハナ'_シ`（話し）|

---

#### `'` の位置 ＝ アクセント型

`'` は「**そのモーラの直後でピッチが下がる**」位置に置きます。

**「花が」と「鼻が」は同じ読みでアクセントだけ違います：**

| 語 | 型 | 音の高低 | 表記 |
|---|---|---|---|
| **花**が | 尾高型 | 低・**高**・低（「が」で下がる） | `ハナ'ガ` |
| **鼻**が | 平板型 | 低・**高**・**高**（下がらない） | `ハナガ'` |

平板型は「アクセント核が存在しない」ことを意味しますが、表記上はフレーズ末尾に `'` を置きます。

---

#### よくある修正パターン

| 問題 | 修正 |
|---|---|
| アクセント核の位置が違う（例: 平板型なのに頭高型） | `'` の位置を正しい場所に移動 |
| フレーズの切れ目が不自然 | `/` を移動・追加・削除 |
| 前後の語に埋もれて聞き取りにくい | `、` でポーズを追加 |
| 固有名詞・数字の読みが誤っている | 読みをカナで修正 |

**ポイント:** 頭高型の特徴が埋もれる場合は `、` で前後から切り離すと聞き取りやすくなります。

---

#### `/` の追加・削除 ― ひとまとまりで読んでほしいとき

`/` で区切るとそれぞれ別のアクセントフレーズとして処理され、境界で読み方が変わることがあります。  
前後の語と**一体のまとまりとして読んでほしい場合は `/` を消して結合**します。

> **例:** 「さっきまでみんなでアクションについて話していた」  
> 修正前: `サ'ッキマデ/ミナ'デ、ア'_クションニ/'ツイテ/ハナ'_シテ/イタ'`  
> 修正後: `サ'ッキマデ/ミナ'デ、ア'_クションニツイテ/ハナ'_シテ/イタ'`  
>  
> `/'ツイテ` を独立したフレーズにすると「ツイテ」で読みが切れます。  
> 「アクションニツイテ」でひとまとまりなので `/` を削除してひとつのフレーズにまとめます。

**注意:** `/` や `、` で区切られた各フレーズには **`'` がちょうど 1 つ**必要です（入力後に自動チェックします）。
"""
        )
    st.divider()

    manifest_map: dict[int, ManifestItem] = {it.item_id: it for it in manifest.items}

    updated_items: list[ItemAnnotation] = []
    all_filled = True

    for idx, item_ann in enumerate(annotation.items):
        m_item = manifest_map.get(item_ann.item_id)
        label = f"[{item_ann.condition_id}] {item_ann.target_word} — {item_ann.sentence[:40]}{'…' if len(item_ann.sentence) > 40 else ''}"

        with st.expander(label, expanded=True):
            st.markdown(f"**文:** {item_ann.sentence}")

            # OpenJTalk の原文読みを参照用に表示（corrected_kana は accent_kana の初期値として反映済み）
            if m_item:
                st.caption(f"OpenJTalk: `{m_item.openjtalk_kana}`")

            accent_kana: str = st.text_input(
                "accent_kana",
                value=item_ann.accent_kana,
                key=f"accent_{idx}",
                placeholder="例: シュウマツニ'/メジロ'ダイニ/デカケタ'",
            )

            if not accent_kana.strip():
                st.warning("入力してください。")
                all_filled = False
            else:
                phrase_errors = _validate_accent_kana(accent_kana)
                if phrase_errors:
                    for err in phrase_errors:
                        st.warning(f"⚠ {err}")
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
    if not all_filled:
        st.warning("入力が完了していないフレーズがあります。全て入力完了後に下の「保存・提出」から提出してください。")
