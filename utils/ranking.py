"""Расчёт взвешенного рейтинга и формирование рейтинговых списков."""

import pandas as pd


def weighted_rating(
    vote_average: float,
    vote_count: float,
    global_mean: float,
    min_votes: float,
) -> float:
    """Рассчитывает взвешенную оценку, снижающую влияние малого числа голосов."""
    if vote_count < 0 or min_votes < 0:
        raise ValueError("Количество голосов и порог не могут быть отрицательными.")

    denominator = vote_count + min_votes
    if denominator == 0:
        return 0.0

    return (
        (vote_count / denominator) * vote_average
        + (min_votes / denominator) * global_mean
    )


def add_weighted_rating(
    movies: pd.DataFrame,
    min_votes: int = 100,
) -> pd.DataFrame:
    """Добавляет к копии каталога столбец weighted_rating."""
    result = movies.copy()
    rated = result.loc[result["vote_count"] > 0, "vote_average"]
    global_mean = float(rated.mean()) if not rated.empty else 0.0

    result["weighted_rating"] = result.apply(
        lambda row: weighted_rating(
            row["vote_average"],
            row["vote_count"],
            global_mean,
            min_votes,
        ),
        axis=1,
    ).round(2)
    return result


def get_top_movies(
    movies: pd.DataFrame,
    ranking_type: str = "Взвешенный рейтинг",
    limit: int = 10,
    min_votes: int = 100,
    genre: str = "Все жанры",
) -> pd.DataFrame:
    """Фильтрует и сортирует фильмы для рейтинговой страницы."""
    if limit < 1:
        raise ValueError("Размер рейтинга должен быть положительным.")

    result = movies[movies["vote_count"] >= min_votes].copy()
    result = result.assign(popularity=result["popularity"].round(2))
    if genre != "Все жанры":
        result = result[result["genres_list"].apply(lambda values: genre in values)]

    columns = {
        "Взвешенный рейтинг": "weighted_rating",
        "Средняя оценка": "vote_average",
        "Популярность": "popularity",
        "Количество голосов": "vote_count",
    }
    if ranking_type not in columns:
        raise ValueError(f"Неизвестный критерий рейтинга: {ranking_type}")

    sort_column = columns[ranking_type]
    if sort_column not in result.columns:
        result = add_weighted_rating(result, min_votes=min_votes)

    return result.sort_values(
        [sort_column, "vote_count"],
        ascending=False,
    ).head(limit).reset_index(drop=True)
