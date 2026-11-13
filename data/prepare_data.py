"""Prepare the TMDB movie data for the dashboard."""

import ast
import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = PROJECT_ROOT / "archive" / "tmdb_5000_movies.csv"
OUTPUT_PATH = Path(__file__).resolve().parent / "movies_cleaned.csv"

NUMERIC_COLUMNS = [
    "budget",
    "revenue",
    "popularity",
    "runtime",
    "vote_average",
    "vote_count",
]


def parse_genres(value: str) -> list[str]:
    """Return genre names from the source JSON-like genre field."""
    if not value or value == "[]":
        return []

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        parsed = ast.literal_eval(value)

    return [item["name"] for item in parsed if item.get("name")]


def prepare_movies() -> pd.DataFrame:
    """Load, clean, transform, and save the dashboard dataset."""
    movies = pd.read_csv(SOURCE_PATH)

    selected_columns = [
        "id",
        "title",
        "genres",
        "original_language",
        "release_date",
        "budget",
        "revenue",
        "runtime",
        "popularity",
        "vote_average",
        "vote_count",
        "status",
    ]
    movies = movies[selected_columns].copy()

    movies["release_date"] = pd.to_datetime(movies["release_date"], errors="coerce")
    movies["release_year"] = movies["release_date"].dt.year.astype("Int64")

    for column in NUMERIC_COLUMNS:
        movies[column] = pd.to_numeric(movies[column], errors="coerce")

    # In this export, zero is used as a missing-data placeholder for these
    # measurements rather than representing a meaningful observed value.
    for column in ["budget", "revenue", "runtime", "vote_average", "vote_count"]:
        movies.loc[movies[column] == 0, column] = pd.NA

    movies["genre_list"] = movies["genres"].map(parse_genres)
    movies["primary_genre"] = movies["genre_list"].map(
        lambda genres: genres[0] if genres else "Unknown"
    )
    movies["genre_list"] = movies["genre_list"].map(
        lambda genres: "|".join(genres) if genres else "Unknown"
    )

    # The core dashboard analyzes released films with known release years.
    movies = movies[
        (movies["status"] == "Released") & movies["release_year"].notna()
    ].copy()

    movies["budget_millions"] = movies["budget"] / 1_000_000
    movies["revenue_millions"] = movies["revenue"] / 1_000_000
    movies["return_multiple"] = (
        movies["revenue"] / movies["budget"]
    ).where(movies["budget"].notna() & (movies["budget"] > 0))

    movies = movies.drop(columns=["genres"])
    movies.to_csv(OUTPUT_PATH, index=False)
    return movies


if __name__ == "__main__":
    cleaned = prepare_movies()
    print(f"Saved {len(cleaned):,} rows to {OUTPUT_PATH}")
    print(f"Columns: {', '.join(cleaned.columns)}")
    print(f"Rows with known budget and revenue: {cleaned[['budget', 'revenue']].notna().all(axis=1).sum():,}")
    print(f"Unknown primary genre rows: {(cleaned['primary_genre'] == 'Unknown').sum():,}")
