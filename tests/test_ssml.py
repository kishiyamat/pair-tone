"""SSML 変換のテスト."""

from __future__ import annotations

import pytest

from annotation_app.polly.ssml import phrase_to_accent_kana, prosody_to_ssml


class TestPhraseToAccentKana:
    def test_no_fall_no_marker(self) -> None:
        # LHH: H→L の遷移がないのでマーカーなし
        assert phrase_to_accent_kana("メジロ", "LHH") == "メジロ"

    def test_fall_after_second_mora(self) -> None:
        # LHL: モーラ2(ジ=H) -> モーラ3(ロ=L) で落下 -> ジの後に '
        assert phrase_to_accent_kana("メジロ", "LHL") == "メジ'ロ"

    def test_fall_after_first_mora(self) -> None:
        # HL: モーラ1(メ=H) -> モーラ2(ジ=L) -> メの後に '
        assert phrase_to_accent_kana("メジ", "HL") == "メ'ジ"

    def test_multiple_falls_only_first(self) -> None:
        # LHLL: H→L は 2→3 の遷移のみ（3→4 は L→L なので対象外）
        assert phrase_to_accent_kana("メジロダ", "LHLL") == "メジ'ロダ"

    def test_with_digraph(self) -> None:
        # シュウ = [シュ, ウ] に対して LH
        assert phrase_to_accent_kana("シュウ", "LH") == "シュウ"

    def test_fully_low(self) -> None:
        assert phrase_to_accent_kana("デカケタ", "LLLL") == "デカケタ"


class TestProsodyToSsml:
    def test_basic_structure(self) -> None:
        ssml = prosody_to_ssml("メジロ", "LHH")
        assert ssml.startswith("<speak>")
        assert ssml.endswith("</speak>")
        assert 'xml:lang="ja-JP"' in ssml

    def test_phoneme_tag_present(self) -> None:
        ssml = prosody_to_ssml("メジロ", "LHH")
        assert 'alphabet="x-amazon-pron-kana"' in ssml
        assert "<phoneme" in ssml

    def test_slash_produces_short_pause(self) -> None:
        ssml = prosody_to_ssml("メジロ/ダイニ", "LHH/LHHL")
        assert '<break time="200ms"/>' in ssml

    def test_comma_produces_long_pause(self) -> None:
        ssml = prosody_to_ssml("メジロ、ダイニ", "LHH、LHHL")
        assert '<break time="500ms"/>' in ssml

    def test_accent_marker_in_ph_attribute(self) -> None:
        # LHL: ジの後にアクセント核マーカー ' が入る
        ssml = prosody_to_ssml("メジロ", "LHL")
        assert "メジ'ロ" in ssml

    def test_multiple_phrases(self) -> None:
        ssml = prosody_to_ssml("シュウマツニ/メジロダイニ/デカケタ", "LHHHH/LHHLLL/LHHH")
        assert ssml.count("<phoneme") == 3
        assert ssml.count("<break") == 2
