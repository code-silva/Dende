import pytest

from app.utils import normalize_search_query, remove_accents


class TestRemoveAccents:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("feijão", "feijao"),
            ("Sabão", "Sabao"),
            ("Águas Claras", "Aguas Claras"),
            ("", ""),
            ("sem acentos", "sem acentos"),
        ],
    )
    def test_removes_accents(self, value, expected):
        assert remove_accents(value) == expected


class TestNormalizeSearchQuery:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("  Feijão  ", "feijao"),
            ("SABÃO", "sabao"),
            (" São José ", "sao jose"),
            ("", ""),
            ("    ", ""),
            (None, ""),
        ],
    )
    def test_normalizes_query(self, value, expected):
        assert normalize_search_query(value) == expected
