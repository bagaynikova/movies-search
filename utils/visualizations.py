"""Графики для аналитической страницы"""

import pandas as pd
import streamlit as st


import altair as alt

def show_rating_charts(movies: pd.DataFrame) -> None:
    """Отображает распределение оценок и средний рейтинг по годам."""
    first, second = st.columns(2)

    with first:
        st.subheader("Распределение оценок")
        ratings = movies.loc[movies["vote_count"] > 0, "vote_average"]
        if ratings.empty:
            st.info("Нет данных об оценках.")
        else:
            histogram = pd.cut(ratings, bins=10, include_lowest=True).value_counts().sort_index()
            chart_data = pd.DataFrame(
                {"Интервал оценки": histogram.index.astype(str), "Количество фильмов": histogram.values}
            ).set_index("Интервал оценки")
            st.bar_chart(chart_data)

    with second:
        st.subheader("Средняя оценка по годам")
        yearly = movies[movies["year"] > 0].groupby("year")["vote_average"].mean()
        #yearly = yearly[yearly.index >= 1950].tail(50)
        
        if yearly.empty:
            st.info("Нет данных для построения графика.")
        else:
            # Преобразуем Series обратно в DataFrame для Altair
            yearly_df = yearly.reset_index()
            yearly_df.columns = ["Год", "Средняя оценка"]

            # Создаем график Altair с жестким ограничением оси Y
            chart = alt.Chart(yearly_df).mark_line(point=False).encode(
                x=alt.X("Год:O", title="Год"), # O означает порядковый тип (чтобы годы не были дробными)
                y=alt.Y(
                    "Средняя оценка:Q", 
                    title="Средняя оценка", 
                    scale=alt.Scale(domain=[0, 10])
                ),
                tooltip=["Год", "Средняя оценка"] # Всплывающая подсказка при наведении
            ).properties(height=350)

            st.altair_chart(chart, use_container_width=True)
