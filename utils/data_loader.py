"""Загрузка и подготовка исходного CSV-файла с фильмами."""

import ast
from pathlib import Path
from typing import Any

import pandas as pd

from utils.languages import LANGUAGE_NAMES

REQUIRED_COLUMNS = {
    "title",
    "genres",
    "production_countries",
    "original_language",
    "release_date",
    "vote_average",
    "vote_count",
    "popularity",
    "runtime",
}


def parse_name_list(value: Any) -> list[str]:
    """Преобразует сериализованный список TMDB в список названий."""
    if isinstance(value, list):
        parsed = value
    elif pd.isna(value) or not str(value).strip():
        return []
    else:
        try:
            parsed = ast.literal_eval(str(value))
        except (ValueError, SyntaxError, TypeError):
            return []

    if not isinstance(parsed, list):
        return []

    names = []
    for item in parsed:
        if isinstance(item, dict) and item.get("name"):
            name = str(item["name"]).strip()
            if name:
                names.append(name)
    return names


def load_movies(path: str | Path) -> pd.DataFrame:
    """Читает CSV и возвращает очищенный датафрейм с полями для приложения."""
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Файл датасета не найден: {file_path}")

    try:
        movies = pd.read_csv(file_path, low_memory=False, encoding="utf-8")
    except UnicodeDecodeError:
        movies = pd.read_csv(file_path, low_memory=False, encoding="latin-1")

    missing = REQUIRED_COLUMNS.difference(movies.columns)
    if missing:
        raise ValueError(
            "В датасете отсутствуют обязательные столбцы: "
            + ", ".join(sorted(missing))
        )

    movies = movies.dropna(subset=["title"]).copy()
    movies["title"] = movies["title"].astype(str).str.strip()
    movies = movies[movies["title"] != ""].copy()

    movies["genres_list"] = movies["genres"].apply(parse_name_list)
    movies["countries_list"] = movies["production_countries"].apply(parse_name_list)
    movies["genre_text"] = movies["genres_list"].apply(", ".join)
    movies["country_text"] = movies["countries_list"].apply(", ".join)

    movies["original_language"] = (
        movies["original_language"].fillna("").astype(str).str.strip().str.lower()
    )
    movies["original_language_name"] = movies["original_language"].map(
        LANGUAGE_NAMES
    ).fillna(movies["original_language"].str.upper())

    for column in ("vote_average", "vote_count", "popularity", "runtime"):
        movies[column] = pd.to_numeric(movies[column], errors="coerce").fillna(0)

    movies["vote_average"] = movies["vote_average"].clip(0, 10).dropna()
    movies["vote_count"] = movies["vote_count"].clip(lower=0).dropna()
    movies["runtime"] = movies["runtime"].clip(0,300).dropna()
    

    release_dates = pd.to_datetime(movies["release_date"], errors="coerce")
    movies["year"] = release_dates.dt.year.fillna(0).astype(int)
    movies = movies[movies["year"].between(1, 2018)]

    if "id" in movies.columns:
        movies = movies.drop_duplicates(subset=["id"], keep="first")

    # Убираем записи без даты из диапазона выбора, оставляя их в каталоге.
    return movies.reset_index(drop=True)