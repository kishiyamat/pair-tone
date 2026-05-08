from annotation_app.ui.prosody_editor import _validate_accent_kana


class TestValidateAccentKana:
    def test_accepts_ascii_apostrophe(self) -> None:
        assert _validate_accent_kana("ハナ'ガ") == []

    def test_warns_for_non_ascii_quote_chars(self) -> None:
        errors = _validate_accent_kana('ハナ”ガ/ハナ`ガ/ハナ"ガ/ハナ´ガ/ハナ’ガ')

        assert "`”` は使えません。アクセント核は ASCII の `'` を使ってください" in errors
        assert "`` ` は使えません。アクセント核は ASCII の `'` を使ってください" not in errors
        assert "`\"` は使えません。アクセント核は ASCII の `'` を使ってください" in errors
        assert "`´` は使えません。アクセント核は ASCII の `'` を使ってください" in errors
        assert "`’` は使えません。アクセント核は ASCII の `'` を使ってください" in errors

    def test_still_reports_missing_ascii_apostrophe(self) -> None:
        errors = _validate_accent_kana("ハナ’ガ")

        assert "`’` は使えません。アクセント核は ASCII の `'` を使ってください" in errors
        assert "`ハナ’ガ` にアクセント核 `'` がありません" in errors

    def test_warns_for_whitespace(self) -> None:
        errors = _validate_accent_kana("ハナ' ガ")

        assert "空白は使えません: `ハナ'[space]ガ` -> `ハナ'ガ`" in errors

    def test_warns_for_invalid_comma_chars(self) -> None:
        errors = _validate_accent_kana("ハナ'ガ,ハナ'ガ，ハナ'ガ")

        assert "`,` は使えません。句切りには `、` を使ってください" in errors
        assert "`，` は使えません。句切りには `、` を使ってください" in errors