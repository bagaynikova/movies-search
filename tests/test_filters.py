import pandas as pd
import pytest

from utils.filters import filter_movies


@pytest.fixture
def sample_movies():
    return pd.DataFrame([
        {
            "title": "The Matrix", "genres_list": ["Action", "Science Fiction"],
            "countries_list": ["United States of America"], "original_language_name": "Английский",
            "year": 1999, "vote_average": 8.7, "runtime": 136,
        },
        {
            "title": "Amelie", "genres_list": ["Comedy", "Romance"],
            "countries_list": ["France"], "original_language_name": "Французский",
            "year": 2001, "vote_average": 8.0, "runtime": 122,
        },
    ])


def test_filter_by_title(sample_movies):
    result = filter_movies(sample_movies, title="matrix")
    assert result["title"].tolist() == ["The Matrix"]


def test_filter_by_multiple_fields(sample_movies):
    result = filter_movies(
        sample_movies,
        genre="Action",
        country="United States of America",
        year_range=(1990, 2000),
        rating_range=(8.0, 9.0),
        runtime_range=(120, 150),
    )
    assert result["title"].tolist() == ["The Matrix"]


def test_filter_by_language(sample_movies):
    result = filter_movies(sample_movies, language="Французский")
    assert result["title"].tolist() == ["Amelie"]