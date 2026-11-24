import pandas as pd

from utils.data_loader import parse_name_list


def test_parse_name_list_reads_tmdb_genres():
    value = "[{'id': 18, 'name': 'Drama'}, {'id': 35, 'name': 'Comedy'}]"
    assert parse_name_list(value) == ["Drama", "Comedy"]


def test_parse_name_list_handles_empty_and_invalid_values():
    assert parse_name_list(None) == []
    assert parse_name_list("") == []
    assert parse_name_list("not a list") == []


def test_parse_name_list_ignores_items_without_names():
    assert parse_name_list("[{'id': 1}, {'name': 'Action'}]") == ["Action"]