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

    def test_ph_keeps_slash(self) -> None:
        input_phrase = "メジロ'/ダイニ'"
        expected = "メジロ'/ダイニ'"
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

    def test_accent_marker_in_ph_not_in_text(self) -> None:
        input_kana = "メジロ'"
        expected = '<speak><lang xml:lang="ja-JP"><phoneme alphabet="x-amazon-pron-kana" ph="メジロ\'">メジロ</phoneme></lang></speak>'
        result = accent_kana_to_ssml(input_kana)
        assert result == expected

    def test_slash_merges_into_single_phoneme(self) -> None:
        # "/" は break なし・単一 phoneme タグ
        input_kana = "メジロ'/ダイニ'"
        expected = '<speak><lang xml:lang="ja-JP"><phoneme alphabet="x-amazon-pron-kana" ph="メジロ\'/ダイニ\'">メジロダイニ</phoneme></lang></speak>'
        result = accent_kana_to_ssml(input_kana)
        assert result == expected

    def test_comma_splits_into_two_phonemes_with_break(self) -> None:
        # "、" は phoneme を分割し 150ms break を挿入
        input_kana = "メジロ'、ダイニ'"
        expected = (
            '<speak><lang xml:lang="ja-JP">'
            '<phoneme alphabet="x-amazon-pron-kana" ph="メジロ\'">メジロ</phoneme>'
            '<break time="150ms"/>'
            '<phoneme alphabet="x-amazon-pron-kana" ph="ダイニ\'">ダイニ</phoneme>'
            '</lang></speak>'
        )
        result = accent_kana_to_ssml(input_kana)
        assert result == expected

    def test_underscore_stripped_from_ph(self) -> None:
        input_kana = "ア'_クション"
        expected = '<speak><lang xml:lang="ja-JP"><phoneme alphabet="x-amazon-pron-kana" ph="ア\'クション">アクション</phoneme></lang></speak>'
        result = accent_kana_to_ssml(input_kana)
        assert result == expected

    def test_multiple_slashes_single_phoneme(self) -> None:
        input_kana = "シュウマツニ'/メジロ'ダイニ/デカケタ'"
        expected = '<speak><lang xml:lang="ja-JP"><phoneme alphabet="x-amazon-pron-kana" ph="シュウマツニ\'/メジロ\'ダイニ/デカケタ\'">シュウマツニメジロダイニデカケタ</phoneme></lang></speak>'
        result = accent_kana_to_ssml(input_kana)
        assert result == expected

    def test_multiple_commas_multiple_phonemes(self) -> None:
        input_kana = "シュウマツニ'、メジロ'ダイニ、デカケタ'"
        expected = (
            '<speak><lang xml:lang="ja-JP">'
            '<phoneme alphabet="x-amazon-pron-kana" ph="シュウマツニ\'">シュウマツニ</phoneme>'
            '<break time="150ms"/>'
            '<phoneme alphabet="x-amazon-pron-kana" ph="メジロ\'ダイニ">メジロダイニ</phoneme>'
            '<break time="150ms"/>'
            '<phoneme alphabet="x-amazon-pron-kana" ph="デカケタ\'">デカケタ</phoneme>'
            '</lang></speak>'
        )
        result = accent_kana_to_ssml(input_kana)
        assert result == expected

    def test_slash_and_comma_combined(self) -> None:
        input_kana = "ア'_クションニ/ツ'イテ、ハナ'_シテ"
        expected = (
            '<speak><lang xml:lang="ja-JP">'
            '<phoneme alphabet="x-amazon-pron-kana" ph="ア\'クションニ/ツ\'イテ">アクションニツイテ</phoneme>'
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

