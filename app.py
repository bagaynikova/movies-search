import pandas as pd

from pathlib import Path

import streamlit as st

from utils.data_loader import load_movies
from utils.filters import filter_movies
from utils.ranking import add_weighted_rating, get_top_movies
from utils.visualizations import show_rating_charts

st.set_page_config(
    page_title="Что посмотреть?",
    page_icon="🍿",
    layout="wide",
)

DATA_PATH = Path(__file__).parent / "data" / "movies.csv"


@st.cache_data(show_spinner="Загружаем каталог фильмов...")
def get_movies() -> pd.DataFrame:
    """Загружает и подготавливает каталог для приложения"""
    return load_movies(DATA_PATH)


def show_movie_cards(movies: pd.DataFrame, limit: int = 30) -> None:
    """Показывает результаты поиска в виде карточек"""
    shown = movies.head(limit)

    for start in range(0, len(shown), 3):
        columns = st.columns(3)
        chunk = shown.iloc[start:start + 3]

        for column, (_, movie) in zip(columns, chunk.iterrows()):
            with column:
                
                year = int(movie["year"]) if movie["year"] else "год неизвестен"
                st.markdown(f"**{movie['title']} ({year})**")
                st.write(f"⭐ Оценка: {movie['vote_average']:.1f}/10")
                st.caption(
                    f"Жанры: {movie['genre_text'] or 'не указаны'}"
                )
                st.caption(
                    f"Страны: {movie['country_text'] or 'не указаны'}"
                )
                runtime = (
                    f"{int(movie['runtime'])} мин."
                    if movie["runtime"] > 0
                    else "не указана"
                )
                st.caption(f"Длительность: {runtime}")
                if movie.get("overview"):
                    with st.expander("Описание"):
                        st.write(movie["overview"])


def search_page(movies: pd.DataFrame) -> None:
    st.header("🔎 Подбор фильма")
    st.write(
        "Используйте один или несколько параметров. "
        "Если фильтр не нужен, оставьте значение «Любой»."
    )

    first, second, third = st.columns(3)
    genres = sorted({item for values in movies["genres_list"] for item in values})
    countries = sorted({item for values in movies["countries_list"] for item in values})
    languages = sorted(
        movies.loc[movies["original_language_name"] != "", "original_language_name"].unique()
    )

    with first:
        title_query = st.text_input("Название фильма", placeholder="Например, Titanic")
        selected_genre = st.selectbox("Жанр", ["Любой"] + genres)
    with second:
        selected_country = st.selectbox("Страна производства", ["Любая"] + countries)
        selected_language = st.selectbox("Язык оригинала", ["Любой"] + languages)
    with third:
        year_min = int(movies.loc[movies["year"] > 0, "year"].min())
        year_max = int(movies["year"].max())
        year_range = st.slider(
            "Годы выпуска",
            min_value=year_min,
            max_value=year_max,
            value=(year_min, year_max),
        )
        rating_range = st.slider(
            "Рейтинг (TMDB)",
            min_value=0.0,
            max_value=10.0,
            value=(0.0, 10.0),
            step=0.5,
        )

    runtime_values = movies.loc[movies["runtime"] > 0, "runtime"]
    runtime_max = min(300, int(runtime_values.max())) if not runtime_values.empty else 300
    runtime_range = st.slider(
        "Длительность, минут",
        min_value=0,
        max_value=max(60, runtime_max),
        value=(0, max(60, runtime_max)),
        step=5,
    )

    filtered = filter_movies(
        movies,
        title=title_query,
        genre=selected_genre,
        country=selected_country,
        language=selected_language,
        year_range=year_range,
        rating_range=rating_range,
        runtime_range=runtime_range,
    )

    st.divider()
    st.metric("Найдено фильмов", f"{len(filtered):,}".replace(",", " "))
    if filtered.empty:
        st.info("По выбранным параметрам фильмы не найдены. Попробуйте изменить фильтры.")
        return

    sort_by = st.selectbox(
        "Сортировать результаты",
        ["Рейтинг", "Популярность", "Количество голосов", "Год выпуска"],
    )
    sort_columns = {
        "Рейтинг": "vote_average",
        "Популярность": "popularity",
        "Количество голосов": "vote_count",
        "Год выпуска": "year",
    }
    filtered = filtered.sort_values(
        sort_columns[sort_by], ascending=False
    ).reset_index(drop=True)

    st.download_button(
        "📥 Скачать найденные фильмы (CSV)",
        data=filtered.drop(columns=["genres_list", "countries_list"], errors="ignore")
        .to_csv(index=False).encode("utf-8-sig"),
        file_name="movie_search_results.csv",
        mime="text/csv",
    )
    show_movie_cards(filtered)

def rating_page(movies: pd.DataFrame) -> None:
    st.header("🏆 Рейтинг фильмов")
    st.write(
        "Рейтинг можно строить по средней оценке, взвешенной оценке, "
        "популярности или количеству пользовательских голосов."
    )

    left, right = st.columns(2)
    with left:
        ranking_type = st.selectbox(
            "Критерий рейтинга",
            ["Взвешенный рейтинг", "Средняя оценка", "Популярность", "Количество голосов"],
        )
        top_count = st.selectbox("Количество фильмов в списке", [10, 20, 50])
    with right:
        min_votes = st.number_input(
            "Минимальное количество голосов",
            min_value=0,
            max_value=100000,
            value=100,
            step=50,
        )
        genre_options = sorted({g for row in movies["genres_list"] for g in row})
        genre = st.selectbox("Жанр", ["Все жанры"] + genre_options)

    ranked = add_weighted_rating(movies, min_votes=int(min_votes))
    top = get_top_movies(
        ranked,
        ranking_type=ranking_type,
        limit=int(top_count),
        min_votes=int(min_votes),
        genre=genre,
    )

    if top.empty:
        st.warning("Нет фильмов, подходящих под выбранные условия.")
        return

    st.dataframe(
        top[
            ["title", "year", "genre_text", "vote_average", "vote_count",
             "weighted_rating", "popularity"]
        ].rename(
            columns={
                "title": "Название",
                "year": "Год",
                "genre_text": "Жанры",
                "vote_average": "Средняя оценка",
                "vote_count": "Количество голосов",
                "weighted_rating": "Взвешенная оценка",
                "popularity": "Популярность",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.download_button(
        "📥 Скачать рейтинг (CSV)",
        data=top.to_csv(index=False).encode("utf-8-sig"),
        file_name="movie_rating.csv",
        mime="text/csv",
    )
    show_movie_cards(top, limit=int(top_count))

    with st.expander("Как рассчитывается взвешенный рейтинг?"):
        st.latex(r"WR = \frac{v}{v+m}R + \frac{m}{v+m}C")
        st.markdown(
            "- **R** — средняя оценка фильма;\n"
            "- **v** — количество голосов за фильм;\n"
            "- **C** — средняя оценка по каталогу;\n"
            "- **m** — минимальный порог голосов.\n\n"
            "Формула уменьшает влияние фильмов с очень малым числом оценок: "
            "их результат частично приближается к средней оценке каталога."
        )


def analytics_page(movies: pd.DataFrame) -> None:
    st.header("📊 Аналитика каталога")
    st.caption("Сводные показатели рассчитываются по загруженному датасету.")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Фильмов в каталоге 43 457")
    col2.metric("Средняя оценка", f"{movies['vote_average'].mean():.2f}/10")
    col3.metric("Медианная длительность", f"{movies.loc[movies.runtime > 0, 'runtime'].median():.0f} мин.")
    col4.metric("Стран производства", movies["countries_list"].explode().nunique())

    show_rating_charts(movies)


def about_page(movies: pd.DataFrame) -> None:
    st.header("ℹ️ О проекте")
    st.markdown(
        """
        
        """
    )
    st.write(f"Размер исходного каталога после очистки: {len(movies):,} записей.")


def main() -> None:
    st.title("Что посмотреть?🍿")
    st.caption("Каталог и подбор фильмов")
    try:
        movies = get_movies()
    except (FileNotFoundError, ValueError) as error:
        st.error(f"Не удалось загрузить каталог: {error}")
        st.stop()

    if movies.empty:
        st.warning("В датасете нет записей, доступных для отображения.")
        st.stop()

    #st.caption(f"В каталоге: {len(movies):,} фильмов".replace(",", " "))
    tabs = st.tabs(["Поиск фильмов", "Рейтинг", "Аналитика", "О проекте"])
    with tabs[0]:
        search_page(movies)
    with tabs[1]:
        rating_page(movies)
    with tabs[2]:
        analytics_page(movies)
    with tabs[3]:
        about_page(movies)


if __name__ == "__main__":
    main()
