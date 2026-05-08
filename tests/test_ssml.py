"""SSML 変換のテスト（accent_kana → SSML）."""

from __future__ import annotations

from annotation_app.polly.ssml import accent_kana_to_ssml


class TestAccentKanaToSsml:
    def test_basic_structure(self) -> None:
        ssml = accent_kana_to_ssml("メジロ'ダイニ")
        assert ssml.startswith("<speak>")
        assert ssml.endswith("</speak>")
        assert 'xml:lang="ja-JP"' in ssml

    def test_phoneme_tag_present(self) -> None:
        ssml = accent_kana_to_ssml("メジロ'ダイニ")
        assert 'alphabet="x-amazon-pron-kana"' in ssml
        assert "<phoneme" in ssml

    def test_accent_marker_in_ph(self) -> None:
        # ' はアクセント核として ph 属性に含まれる
        ssml = accent_kana_to_ssml("メジロ'ダイニ")
        assert "メジロ'ダイニ" in ssml

    def test_accent_marker_stripped_from_text(self) -> None:
        # 表示テキストには ' が含まれない
        ssml = accent_kana_to_ssml("メジロ'")
        # <phoneme ... ph="メジロ'">メジロ</phoneme> の形
        assert ">メジロ<" in ssml

    def test_slash_produces_no_pause(self) -> None:
        # "/" はアクセント句境界のみ。Polly に break を挿入しない
        ssml = accent_kana_to_ssml("メジロ'/ダイニ'")
        assert "<break" not in ssml
        assert ssml.count("<phoneme") == 2

    def test_comma_produces_long_pause(self) -> None:
        ssml = accent_kana_to_ssml("メジロ'、ダイニ'")
        assert '<break time="150ms"/>' in ssml

    def test_multiple_phrases(self) -> None:
        ssml = accent_kana_to_ssml("シュウマツニ'/メジロ'ダイニ/デカケタ'")
        assert ssml.count("<phoneme") == 3
        # "/" はbreak なし
        assert "<break" not in ssml

    def test_underscore_stripped_from_ph(self) -> None:
        # _ は ph 属性から除去される
        ssml = accent_kana_to_ssml("ア'_クション")
        assert "_" not in ssml

    def test_no_accent_marker(self) -> None:
        # ' なしでもエラーにならない
        ssml = accent_kana_to_ssml("デカケタ")
        assert "<phoneme" in ssml

    def test_empty_string(self) -> None:
        ssml = accent_kana_to_ssml("")
        assert "<speak>" in ssml
