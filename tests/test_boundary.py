"""境界整合性検証のテスト."""

from __future__ import annotations

from annotation_app.validation.boundary import validate_boundary_layout


class TestValidBoundaryLayout:
    def test_single_phrase_ok(self) -> None:
        errors = validate_boundary_layout("メジロ", "LHH")
        assert errors == []

    def test_multiple_slash_ok(self) -> None:
        # シュウマツニ=5, LHHHH=5 / メジロダイニ=6, LHHLLL=6 / デカケタ=4, LHHH=4
        errors = validate_boundary_layout(
            "シュウマツニ/メジロダイニ/デカケタ",
            "LHHHH/LHHLLL/LHHH",
        )
        assert errors == []

    def test_comma_boundary_ok(self) -> None:
        # メジロ=3, LHH=3 / ダイニ=3, LHH=3
        errors = validate_boundary_layout("メジロ、ダイニ", "LHH、LHH")
        assert errors == []

    def test_mixed_boundaries_ok(self) -> None:
        # メジロ=3, LHH=3 / ダイニ=3, LHH=3 / デカケタ=4, LHHH=4
        errors = validate_boundary_layout("メジロ/ダイニ、デカケタ", "LHH/LHH、LHHH")
        assert errors == []


class TestSeparatorCountMismatch:
    def test_extra_slash_in_kana(self) -> None:
        errors = validate_boundary_layout("メジロ/ダイニ", "LHHLLL")
        assert len(errors) >= 1
        assert any("区切り記号" in e.message for e in errors)

    def test_extra_slash_in_pattern(self) -> None:
        errors = validate_boundary_layout("メジロダイニ", "LHH/LLL")
        assert len(errors) >= 1


class TestSeparatorTypeMismatch:
    def test_slash_vs_comma(self) -> None:
        errors = validate_boundary_layout("メジロ/ダイニ", "LHH、LHHL")
        assert any("区切り記号" in e.message for e in errors)


class TestMoraCountMismatch:
    def test_kana_shorter(self) -> None:
        # メジロ=3 vs LHHL=4
        errors = validate_boundary_layout("メジロ", "LHHL")
        assert len(errors) == 1
        assert "モーラ" in errors[0].message
        assert errors[0].phrase_index == 0

    def test_kana_longer(self) -> None:
        # メジロダイ=5 vs LHH=3
        errors = validate_boundary_layout("メジロダイ", "LHH")
        assert len(errors) == 1
        assert "モーラ" in errors[0].message

    def test_second_phrase_mismatch(self) -> None:
        errors = validate_boundary_layout("メジロ/ダイ", "LHH/LHHLL")
        assert any(e.phrase_index == 1 for e in errors)


class TestInvalidPatternChars:
    def test_invalid_char_in_pattern(self) -> None:
        errors = validate_boundary_layout("メジロ", "LXH")
        assert any("無効な文字" in e.message for e in errors)

    def test_lowercase_invalid(self) -> None:
        errors = validate_boundary_layout("メジロ", "lhh")
        assert any("無効な文字" in e.message for e in errors)
