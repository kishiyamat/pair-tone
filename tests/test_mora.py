"""モーラ分割・カウントのテスト."""

from __future__ import annotations

import pytest

from annotation_app.validation.mora import count_morae, split_morae, strip_boundaries


class TestSplitMorae:
    def test_simple_katakana(self) -> None:
        assert split_morae("カタカナ") == ["カ", "タ", "カ", "ナ"]

    def test_digraph_shu(self) -> None:
        # シュ は 1 モーラ
        assert split_morae("シュ") == ["シュ"]

    def test_digraph_in_word(self) -> None:
        # シュウ = シュ + ウ = 2 モーラ
        assert split_morae("シュウ") == ["シュ", "ウ"]

    def test_full_word(self) -> None:
        # シュウマツニ = シュ・ウ・マ・ツ・ニ = 5 モーラ
        assert split_morae("シュウマツニ") == ["シュ", "ウ", "マ", "ツ", "ニ"]

    def test_sokuon_is_independent(self) -> None:
        # ッ は独立モーラ
        assert split_morae("キッテ") == ["キ", "ッ", "テ"]

    def test_moraic_nasal_is_independent(self) -> None:
        # ン は独立モーラ
        assert split_morae("ホン") == ["ホ", "ン"]

    def test_underscore_ignored(self) -> None:
        # _ は無視する（無声化マーク）
        assert split_morae("キ_コ") == ["キ", "コ"]

    def test_underscore_between_digraph(self) -> None:
        assert split_morae("シュ_ウ") == ["シュ", "ウ"]

    def test_multiple_small_kana(self) -> None:
        # チョウ = チョ + ウ
        assert split_morae("チョウ") == ["チョ", "ウ"]

    def test_empty_string(self) -> None:
        assert split_morae("") == []


class TestCountMorae:
    def test_shu_u_ma_tsu_ni(self) -> None:
        assert count_morae("シュウマツニ") == 5

    def test_me_ji_ro_da_i_ni(self) -> None:
        assert count_morae("メジロダイニ") == 6

    def test_de_ka_ke_ta(self) -> None:
        assert count_morae("デカケタ") == 4

    def test_with_underscore(self) -> None:
        assert count_morae("キ_コ") == 2


class TestStripBoundaries:
    def test_remove_slash(self) -> None:
        assert strip_boundaries("ア/イ/ウ") == "アイウ"

    def test_remove_comma(self) -> None:
        assert strip_boundaries("ア、イ") == "アイ"

    def test_mixed(self) -> None:
        assert strip_boundaries("ア/イ、ウ") == "アイウ"

    def test_no_boundaries(self) -> None:
        assert strip_boundaries("アイウ") == "アイウ"
