from tools.audit_terms import hits, load_terms


def test_audit_matches_plain_and_regex_terms(tmp_path):
    terms = tmp_path / "terms.txt"
    terms.write_text("# comment\nSecret Name\nre:user-[0-9]+\n", encoding="utf-8")
    pats = load_terms(terms)
    assert hits("by SECRET name", pats) == ["Secret Name"]
    assert hits("folder user-42", pats) == ["re:user-[0-9]+"]
    assert hits("clean line", pats) == []
