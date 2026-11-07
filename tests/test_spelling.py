from core.search import correct_spelling


def test_correct_text_is_unchanged():
    result = correct_spelling("cloud computing")
    assert result["corrected_text"] == "cloud computing"
    assert result["has_corrections"] is False


def test_misspelled_word_is_corrected():
    result = correct_spelling("clowd computng")
    assert result["has_corrections"] is True
    assert "computing" in result["corrected_text"]
