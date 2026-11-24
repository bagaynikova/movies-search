"""Функции фильтрации каталога фильмов"""

import pandas as pd


def filter_movies(
    movies: pd.DataFrame,
    title: str = "",
    genre: str = "Любой",
    country: str = "Любая",
    language: str = "Любой",
    year_range: tuple[int, int] | None = None,
    rating_range: tuple[float, float] | None = None,
    runtime_range: tuple[int, int] | None = None,
) -> pd.DataFrame:
    """Возвращает копию каталога, соответствующую всем заданным фильтрам"""
    result = movies.copy()

    if title.strip():
        result = result[
            result["title"].str.contains(title.strip(), case=False, na=False, regex=False)
        ]

    if genre != "Любой":
        result = result[result["genres_list"].apply(lambda values: genre in values)]

    if country != "Любая":
        result = result[result["countries_list"].apply(lambda values: country in values)]

    if language != "Любой":
        result = result[result["original_language_name"] == language]

    if year_range is not None:
        start, end = year_range
        result = result[result["year"].between(start, end) & (result["year"] > 0)]

    if rating_range is not None:
        low, high = rating_range
        result = result[result["vote_average"].between(low, high)]

    if runtime_range is not None:
        low, high = runtime_range
        # Нулевая длительность означает отсутствие значения и не проходит фильтр
        result = result[
            (result["runtime"] > 0) & result["runtime"].between(low, high)
        ]

    return result.reset_index(drop=True)
