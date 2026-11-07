from core.embedding import chunk_text


def test_empty_text_returns_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("\n\n   \n") == []


def test_headings_become_their_own_chunks():
    text = "INTRODUCTION\nThis is the body of the first section.\nMethods:\nMore body text."
    assert chunk_text(text) == [
        "INTRODUCTION",
        "This is the body of the first section.",
        "Methods:",
        "More body text.",
    ]


def test_consecutive_lines_are_merged_up_to_max_length():
    text = "alpha beta\ngamma delta\nepsilon zeta"
    assert chunk_text(text, max_length=500) == ["alpha beta gamma delta epsilon zeta"]


def test_chunks_respect_max_length():
    lines = ["word " * 10 for _ in range(20)]  # 50 chars per line
    chunks = chunk_text("\n".join(lines), max_length=120)
    assert len(chunks) > 1
    assert all(len(chunk) <= 120 for chunk in chunks)
