"""SSML 変換のテスト（accent_kana → SSML）."""

from __future__ import annotations

from annotation_app.polly.ssml import _phrase_to_ph, _phrase_to_text, accent_kana_to_ssml


class TestPhraseToPhAndText:
    def test_ph_strips_underscore(self) -> None:
        input_phrase = "ア'_クション"
        expected = "ア'クション"
        result = _phrase_to_ph(input_phrase)
        assert result == expected

    def test_ph_keeps_accent_marker(self) -> None:
        input_phrase = "ハナ'ガ"
        expected = "ハナ'ガ"
        result = _phrase_to_ph(input_phrase)
        assert result == expected

    def test_ph_strips_trailing_accent(self) -> None:
        # OpenJTalk 末尾 ' は 0型（平板型）マーカーであり Polly に渡すと末尾下降と誤解釈される
        assert _phrase_to_ph("イタ'") == "イタ"
        assert _phrase_to_ph("エンシュツオ'") == "エンシュツオ"
        # 句中の ' はアクセント核なので保持する
        assert _phrase_to_ph("ハナ'シテ") == "ハナ'シテ"

    def test_ph_strips_slash(self) -> None:
        # _phrase_to_ph は / を受け取らない（分割後に呼ばれる）が、防御的に除去はしない。
        # このテストは「/ を含む入力を渡しても _ だけが除去され / は残る」ことを確認する。
        input_phrase = "ア'_クション/ツ'イテ"
        expected = "ア'クション/ツ'イテ"  # _ のみ除去
        result = _phrase_to_ph(input_phrase)
        assert result == expected

    def test_text_strips_accent_marker(self) -> None:
        input_phrase = "メジロ'"
        expected = "メジロ"
        result = _phrase_to_text(input_phrase)
        assert result == expected

    def test_text_strips_underscore(self) -> None:
        input_phrase = "ハナ'_シ"
        expected = "ハナシ"
        result = _phrase_to_text(input_phrase)
        assert result == expected

    def test_text_strips_slash(self) -> None:
        input_phrase = "メジロ'/ダイニ'"
        expected = "メジロダイニ"
        result = _phrase_to_text(input_phrase)
        assert result == expected


class TestAccentKanaToSsml:
    def test_basic_single_phrase(self) -> None:
        input_kana = "ハナ'ガ"
        expected = '<speak><lang xml:lang="ja-JP"><phoneme alphabet="x-amazon-pron-kana" ph="ハナ\'ガ">ハナガ</phoneme></lang></speak>'
        result = accent_kana_to_ssml(input_kana)
        assert result == expected

    def test_trailing_accent_stripped_from_ph(self) -> None:
        # 末尾 ' は 0型マーカー → ph 属性から除去。テキストノードも ' なし
        input_kana = "メジロ'"
        expected = '<speak><lang xml:lang="ja-JP"><phoneme alphabet="x-amazon-pron-kana" ph="メジロ">メジロ</phoneme></lang></speak>'
        result = accent_kana_to_ssml(input_kana)
        assert result == expected

    def test_slash_splits_into_separate_phonemes(self) -> None:
        # "/" で分割 → 別々の phoneme タグ（空白なし）
        # 末尾 ' は 0型マーカーなので ph 属性から除去
        input_kana = "メジロ'/ダイニ'"
        expected = (
            '<speak><lang xml:lang="ja-JP">'
            '<phoneme alphabet="x-amazon-pron-kana" ph="メジロ">メジロ</phoneme>'
            '<phoneme alphabet="x-amazon-pron-kana" ph="ダイニ">ダイニ</phoneme>'
            '</lang></speak>'
        )
        result = accent_kana_to_ssml(input_kana)
        assert result == expected

    def test_comma_splits_into_two_phonemes_with_break(self) -> None:
        # "、" は phoneme を分割し 150ms break を挿入
        # 末尾 ' は 0型マーカーなので ph から除去
        input_kana = "メジロ'、ダイニ'"
        expected = (
            '<speak><lang xml:lang="ja-JP">'
            '<phoneme alphabet="x-amazon-pron-kana" ph="メジロ">メジロ</phoneme>'
            '<break time="150ms"/>'
            '<phoneme alphabet="x-amazon-pron-kana" ph="ダイニ">ダイニ</phoneme>'
            '</lang></speak>'
        )
        result = accent_kana_to_ssml(input_kana)
        assert result == expected

    def test_underscore_stripped_from_ph(self) -> None:
        input_kana = "ア'_クション"
        expected = '<speak><lang xml:lang="ja-JP"><phoneme alphabet="x-amazon-pron-kana" ph="ア\'クション">アクション</phoneme></lang></speak>'
        result = accent_kana_to_ssml(input_kana)
        assert result == expected

    def test_multiple_slashes_multiple_phonemes(self) -> None:
        # 末尾 ' を持つフレーズは ph から除去
        # 句中の ' （メジロ'ダイニ）は保持
        input_kana = "シュウマツニ'/メジロ'ダイニ/デカケタ'"
        expected = (
            '<speak><lang xml:lang="ja-JP">'
            '<phoneme alphabet="x-amazon-pron-kana" ph="シュウマツニ">シュウマツニ</phoneme>'
            '<phoneme alphabet="x-amazon-pron-kana" ph="メジロ\'ダイニ">メジロダイニ</phoneme>'
            '<phoneme alphabet="x-amazon-pron-kana" ph="デカケタ">デカケタ</phoneme>'
            '</lang></speak>'
        )
        result = accent_kana_to_ssml(input_kana)
        assert result == expected

    def test_multiple_commas_multiple_phonemes(self) -> None:
        input_kana = "シュウマツニ'、メジロ'ダイニ、デカケタ'"
        expected = (
            '<speak><lang xml:lang="ja-JP">'
            '<phoneme alphabet="x-amazon-pron-kana" ph="シュウマツニ">シュウマツニ</phoneme>'
            '<break time="150ms"/>'
            '<phoneme alphabet="x-amazon-pron-kana" ph="メジロ\'ダイニ">メジロダイニ</phoneme>'
            '<break time="150ms"/>'
            '<phoneme alphabet="x-amazon-pron-kana" ph="デカケタ">デカケタ</phoneme>'
            '</lang></speak>'
        )
        result = accent_kana_to_ssml(input_kana)
        assert result == expected

    def test_slash_and_comma_combined(self) -> None:
        # / → 途中空白なしの別 phoneme、、→ break
        input_kana = "ア'_クションニ/ツ'イテ、ハナ'_シテ"
        expected = (
            '<speak><lang xml:lang="ja-JP">'
            '<phoneme alphabet="x-amazon-pron-kana" ph="ア\'クションニ">アクションニ</phoneme>'
            '<phoneme alphabet="x-amazon-pron-kana" ph="ツ\'イテ">ツイテ</phoneme>'
            '<break time="150ms"/>'
            '<phoneme alphabet="x-amazon-pron-kana" ph="ハナ\'シテ">ハナシテ</phoneme>'
            '</lang></speak>'
        )
        result = accent_kana_to_ssml(input_kana)
        assert result == expected

    def test_empty_string(self) -> None:
        input_kana = ""
        expected = '<speak><lang xml:lang="ja-JP"></lang></speak>'
        result = accent_kana_to_ssml(input_kana)
        assert result == expected

