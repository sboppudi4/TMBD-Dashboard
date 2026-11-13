"""Interactive TMDB movie dashboard."""

from __future__ import annotations

import math
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, State, ctx, dcc, html, no_update


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "movies_cleaned.csv"


# Load the prepared dataset once when the application starts so callbacks can
# reuse the same in-memory frame for consistent filtering and chart updates.
def load_movies() -> pd.DataFrame:
    movies = pd.read_csv(DATA_PATH)
    movies["id"] = movies["id"].astype(str)
    for column in [
        "budget_millions",
        "revenue_millions",
        "popularity",
        "vote_average",
        "release_year",
    ]:
        movies[column] = pd.to_numeric(movies[column], errors="coerce")
    return movies


# Group less frequent primary genres into one readable category for the chart.
MOVIES = load_movies()
TOP_GENRES = (
    MOVIES["primary_genre"]
    .dropna()
    .value_counts()
    .head(6)
    .index
    .tolist()
)
GENRES = TOP_GENRES + ["Other"]
MOVIES["genre_group"] = MOVIES["primary_genre"].apply(
    lambda genre: genre if genre in TOP_GENRES else "Other"
)
MAX_BUDGET = math.ceil(MOVIES["budget_millions"].max())
MAX_REVENUE = math.ceil(MOVIES["revenue_millions"].max())
MIN_YEAR = int(MOVIES["release_year"].min())
MAX_YEAR = int(MOVIES["release_year"].max())
# Track the financial-data coverage shown in the dashboard status message.
COMPLETE_FINANCIAL_IDS = set(
    MOVIES.loc[
        MOVIES[["budget_millions", "revenue_millions"]].notna().all(axis=1),
        "id",
    ]
)
MISSING_FINANCIAL_COUNT = MOVIES["id"].nunique() - len(COMPLETE_FINANCIAL_IDS)


def full_filter_state() -> dict:
    """Return the default state used by the initial view and reset button."""
    return {
        "genre": None,
        "budget": [0, MAX_BUDGET],
        "revenue": [0, MAX_REVENUE],
        "year": [MIN_YEAR, MAX_YEAR],
        "rating": [0, 10],
        "selected_ids": None,
    }


def ids_from_scatter(selection: dict | None) -> set[str]:
    """Extract stable movie IDs from a Plotly box or lasso selection."""
    if not selection:
        return set()
    return {
        str(point["customdata"][0])
        for point in selection.get("points", [])
        if point.get("customdata")
    }


def ids_from_genre(click_data: dict | None) -> set[str]:
    """Return movie IDs belonging to the genre bar that was clicked."""
    if not click_data or not click_data.get("points"):
        return set()
    genre = click_data["points"][0].get("y")
    if not genre:
        return set()
    return set(MOVIES.loc[MOVIES["genre_group"] == genre, "id"])


def ids_from_timeline(selection: dict | None) -> set[str]:
    """Return movie IDs from the release years selected on the timeline."""
    if not selection:
        return set()
    years = {
        int(point["x"])
        for point in selection.get("points", [])
        if point.get("x") is not None
    }
    return set(MOVIES.loc[MOVIES["release_year"].isin(years), "id"])


def ids_from_rating(click_data: dict | None) -> set[str]:
    """Extract the movie IDs stored in a clicked rating bin."""
    if not click_data:
        return set()
    ids: set[str] = set()
    for point in click_data.get("points", []):
        customdata = point.get("customdata")
        if isinstance(customdata, list):
            values = customdata[0] if len(customdata) == 1 else customdata
            if isinstance(values, list):
                ids.update(str(movie_id) for movie_id in values)
            else:
                ids.add(str(values))
        elif customdata is not None:
            ids.add(str(customdata))
    return ids


def ids_for_controls(state: dict) -> set[str]:
    """Apply explicit controls while excluding missing numeric values."""
    selected = MOVIES[
        MOVIES["budget_millions"].between(*state["budget"])
        & MOVIES["revenue_millions"].between(*state["revenue"])
        & MOVIES["release_year"].between(*state["year"])
        & MOVIES["vote_average"].between(*state["rating"])
    ]
    if state["genre"]:
        selected = selected[selected["genre_group"] == state["genre"]]
    return set(selected["id"])


def empty_figure(message: str) -> go.Figure:
    """Create a consistent placeholder when a chart has no matching data."""
    figure = go.Figure()
    figure.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={"size": 16, "color": "#64748B"},
    )
    figure.update_layout(
        template="plotly_white",
        xaxis={"visible": False},
        yaxis={"visible": False},
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
    )
    return figure


def scatter_figure(data: pd.DataFrame) -> go.Figure:
    """Build the primary financial comparison and its visual encodings."""
    data = data.dropna(
        subset=["budget_millions", "revenue_millions", "vote_average"]
    )
    if data.empty:
        return empty_figure("No complete financial and rating data matches the filters")
    figure = px.scatter(
        data,
        x="budget_millions",
        y="revenue_millions",
        color="vote_average",
        color_continuous_scale="Viridis",
        size="popularity",
        size_max=30,
        render_mode="svg",
        custom_data=["id"],
        hover_name="title",
        hover_data={
            "budget_millions": ":.1f",
            "revenue_millions": ":.1f",
            "vote_average": ":.1f",
            "popularity": ":.1f",
            "id": False,
        },
        labels={
            "budget_millions": "Budget ($ millions)",
            "revenue_millions": "Revenue ($ millions)",
            "vote_average": "Vote average",
        },
        title="Budget vs. Revenue",
        template="plotly_white",
    )
    figure.update_traces(
        selected={"marker": {"opacity": 1}},
        unselected={"marker": {"opacity": 0.25}},
    )
    figure.update_layout(
        uirevision="dataset",
        dragmode="select",
        margin={"l": 55, "r": 20, "t": 50, "b": 50},
        coloraxis_colorbar={
            "title": "Vote average",
            "tickmode": "array",
            "tickvals": [0, 2, 4, 6, 8, 10],
        },
    )
    return figure


def genre_figure(data: pd.DataFrame) -> go.Figure:
    """Build the grouped genre comparison using average revenue."""
    summary = (
        data.dropna(subset=["revenue_millions"])
        .groupby("genre_group", as_index=False)["revenue_millions"]
        .mean()
        .sort_values("revenue_millions")
    )
    if summary.empty:
        return empty_figure("No revenue data matches the filters")
    figure = px.bar(
        summary,
        x="revenue_millions",
        y="genre_group",
        orientation="h",
        custom_data=["genre_group"],
        color_discrete_sequence=["#005A70"],
        labels={
            "revenue_millions": "Average revenue ($ millions)",
            "genre_group": "",
        },
        title="Average Revenue by Primary Genre",
        template="plotly_white",
    )
    figure.update_layout(
        uirevision="dataset",
        clickmode="event+select",
        margin={"l": 90, "r": 20, "t": 50, "b": 50},
    )
    return figure


def timeline_figure(data: pd.DataFrame) -> go.Figure:
    """Build the chronological average-revenue view."""
    summary = (
        data.groupby("release_year", as_index=False)["revenue_millions"]
        .mean()
        .dropna()
        .sort_values("release_year")
    )
    if summary.empty:
        return empty_figure("No revenue data matches the filters")
    figure = px.line(
        summary,
        x="release_year",
        y="revenue_millions",
        markers=True,
        custom_data=["release_year"],
        color_discrete_sequence=["#1B7837"],
        labels={
            "release_year": "Release year",
            "revenue_millions": "Average revenue ($ millions)",
        },
        title="Average Revenue Trend Over Time",
        template="plotly_white",
    )
    figure.update_traces(
        mode="lines+markers",
        marker={"size": 8},
        selected={"marker": {"opacity": 1}},
        unselected={"marker": {"opacity": 0.25}},
    )
    figure.update_layout(
        uirevision="dataset",
        margin={"l": 55, "r": 20, "t": 50, "b": 50},
    )
    return figure


def rating_figure(data: pd.DataFrame) -> go.Figure:
    """Build the half-point vote-average distribution."""
    ratings = data.dropna(subset=["vote_average"]).copy()
    if ratings.empty:
        return empty_figure("No ratings match the filters")
    ratings["rating_bin"] = (ratings["vote_average"] * 2).round() / 2
    summary = (
        ratings.groupby("rating_bin", as_index=False)
        .agg(movie_count=("id", "size"), rating_ids=("id", list))
        .sort_values("rating_bin")
    )
    figure = px.bar(
        summary,
        x="rating_bin",
        y="movie_count",
        custom_data=["rating_ids"],
        color_discrete_sequence=["#542788"],
        labels={"rating_bin": "Vote average", "movie_count": "Movie count"},
        title="Movie Rating Distribution",
        template="plotly_white",
    )
    figure.update_layout(
        uirevision="dataset",
        clickmode="event+select",
        bargap=0.08,
        margin={"l": 55, "r": 20, "t": 50, "b": 50},
    )
    return figure


def metric_card(label: str, component_id: str) -> dbc.Col:
    """Return a reusable KPI card with a callback-populated value."""
    return dbc.Col(
        dbc.Card(
            dbc.CardBody(
                [
                    html.P(label, className="text-muted mb-1"),
                    html.H3(id=component_id, className="mb-0"),
                ]
            ),
            className="h-100 shadow-sm",
        ),
        xs=12,
        md=4,
    )


app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    title="TMDB Movie Financial & Reception Dashboard",
)

# The layout follows an overview-to-details hierarchy: controls, KPIs, then
# coordinated analytical views.
app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1(
                            "TMDB Movie Financial & Reception Dashboard",
                            className="mt-3 mb-1",
                        ),
                        html.P(
                            "Explore how budget, revenue, genre, release year, and ratings relate.",
                            className="text-muted",
                        ),
                    ],
                    md=8,
                ),
            ],
            className="align-items-start",
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                html.H4("Filters", className="card-title mb-0"),
                                md=8,
                            ),
                            dbc.Col(
                                dbc.Button(
                                    "Reset All Filters",
                                    id="reset-btn",
                                    color="danger",
                                    className="w-100 w-md-auto",
                                ),
                                md=4,
                                className="text-md-end mt-2 mt-md-0",
                            ),
                        ],
                        className="align-items-center filter-card-header",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label(
                                        "Primary genre",
                                        className="filter-label",
                                    ),
                                    dcc.Dropdown(
                                        id="genre-filter",
                                        options=[{"label": g, "value": g} for g in GENRES],
                                        placeholder="All genres",
                                        clearable=True,
                                        className="filter-dropdown",
                                    ),
                                ],
                                lg=3,
                                className="filter-control",
                            ),
                            dbc.Col(
                                [
                                    html.Label(
                                        "Budget ($ millions)",
                                        className="filter-label",
                                    ),
                                    dcc.RangeSlider(
                                        id="budget-filter",
                                        min=0,
                                        max=MAX_BUDGET,
                                        value=[0, MAX_BUDGET],
                                        marks=None,
                                        tooltip={"placement": "top", "always_visible": False},
                                        className="filter-slider",
                                    ),
                                ],
                                lg=3,
                                className="filter-control",
                            ),
                            dbc.Col(
                                [
                                    html.Label(
                                        "Revenue ($ millions)",
                                        className="filter-label",
                                    ),
                                    dcc.RangeSlider(
                                        id="revenue-filter",
                                        min=0,
                                        max=MAX_REVENUE,
                                        value=[0, MAX_REVENUE],
                                        marks=None,
                                        tooltip={"placement": "top", "always_visible": False},
                                        className="filter-slider",
                                    ),
                                ],
                                lg=3,
                                className="filter-control",
                            ),
                            dbc.Col(
                                [
                                    html.Label(
                                        "Release year",
                                        className="filter-label",
                                    ),
                                    dcc.RangeSlider(
                                        id="year-filter",
                                        min=MIN_YEAR,
                                        max=MAX_YEAR,
                                        value=[MIN_YEAR, MAX_YEAR],
                                        marks=None,
                                        tooltip={"placement": "top", "always_visible": False},
                                        className="filter-slider",
                                    ),
                                ],
                                lg=3,
                                className="filter-control",
                            ),
                        ],
                        className="g-3 filter-grid",
                    ),
                    html.P(
                        "Movies without recorded budget or revenue are excluded "
                        "from financial charts and range filters.",
                        className="text-muted small mb-0 mt-3",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label(
                                        "Vote average",
                                        className="filter-label",
                                    ),
                                    dcc.RangeSlider(
                                        id="rating-filter",
                                        min=0,
                                        max=10,
                                        step=0.1,
                                        value=[0, 10],
                                        marks=None,
                                        tooltip={"placement": "top", "always_visible": False},
                                        className="filter-slider",
                                    ),
                                ],
                                lg=12,
                                className="filter-control",
                            ),
                        ],
                        className="g-3 filter-grid filter-grid-secondary",
                    ),
                ]
            ),
            className="shadow-sm mb-4 filter-card",
        ),
        dbc.Row(
            [
            metric_card("Movies with Complete Financial Data", "kpi-count"),
                metric_card("Average Revenue", "kpi-revenue"),
                metric_card("Average Vote Rating", "kpi-rating"),
            ],
            className="g-3 mb-4",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4("Budget vs. Revenue", className="card-title"),
                                html.P(
                                    "Use the filters above to compare movie groups. Viridis color encodes vote average.",
                                    className="text-muted small",
                                ),
                                dcc.Graph(
                                    id="scatter-plot",
                                    config={"displayModeBar": True},
                                ),
                            ]
                        ),
                        className="shadow-sm h-100",
                    ),
                    lg=7,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4(
                                    "Average Revenue by Primary Genre",
                                    className="card-title",
                                ),
                                html.P(
                                    "The six largest primary genres are shown individually; the rest are grouped into Other.",
                                    className="text-muted small",
                                ),
                                dcc.Graph(
                                    id="genre-bar-chart",
                                    config={"displayModeBar": False},
                                ),
                            ]
                        ),
                        className="shadow-sm h-100",
                    ),
                    lg=5,
                ),
            ],
            className="g-3 mb-4",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4(
                                    "Average Revenue Trend Over Time",
                                    className="card-title",
                                ),
                                html.P(
                                    "Use the release-year filter to compare eras.",
                                    className="text-muted small",
                                ),
                                dcc.Graph(
                                    id="timeline-chart",
                                    config={"displayModeBar": True},
                                ),
                            ]
                        ),
                        className="shadow-sm h-100",
                    ),
                    lg=7,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4(
                                    "Movie Rating Distribution",
                                    className="card-title",
                                ),
                                html.P(
                                    "Use the vote-average filter to isolate ratings.",
                                    className="text-muted small",
                                ),
                                dcc.Graph(
                                    id="rating-histogram",
                                    config={"displayModeBar": False},
                                ),
                            ]
                        ),
                        className="shadow-sm h-100",
                    ),
                    lg=5,
                ),
            ],
            className="g-3 pb-4",
        ),
        dcc.Store(id="filter-store", data=full_filter_state()),
        html.P(id="selection-status", className="text-muted small"),
    ],
    fluid=True,
    className="px-3 px-md-4",
)


@app.callback(
    Output("filter-store", "data"),
    Output("genre-filter", "value"),
    Output("budget-filter", "value"),
    Output("revenue-filter", "value"),
    Output("year-filter", "value"),
    Output("rating-filter", "value"),
    Output("scatter-plot", "selectedData"),
    Output("timeline-chart", "selectedData"),
    Output("genre-bar-chart", "clickData"),
    Output("rating-histogram", "clickData"),
    Input("genre-filter", "value"),
    Input("budget-filter", "value"),
    Input("revenue-filter", "value"),
    Input("year-filter", "value"),
    Input("rating-filter", "value"),
    Input("scatter-plot", "selectedData"),
    Input("genre-bar-chart", "clickData"),
    Input("timeline-chart", "selectedData"),
    Input("rating-histogram", "clickData"),
    Input("reset-btn", "n_clicks"),
    State("filter-store", "data"),
    prevent_initial_call=False,
)
def update_filter_state(
    genre: str | None,
    budget_range: list[float],
    revenue_range: list[float],
    year_range: list[float],
    rating_range: list[float],
    scatter_selection: dict | None,
    genre_click: dict | None,
    timeline_selection: dict | None,
    rating_click: dict | None,
    _reset_clicks: int,
    previous: dict | None,
) -> tuple:
    """Combine control and chart interactions into one persistent filter state."""
    if ctx.triggered_id == "reset-btn":
        defaults = full_filter_state()
        return (
            defaults,
            defaults["genre"],
            defaults["budget"],
            defaults["revenue"],
            defaults["year"],
            defaults["rating"],
            None,
            None,
            None,
            None,
        )

    state = {
        "genre": genre,
        "budget": budget_range,
        "revenue": revenue_range,
        "year": year_range,
        "rating": rating_range,
        "selected_ids": previous.get("selected_ids") if previous else None,
    }
    base_ids = ids_for_controls(state)
    if ctx.triggered_id == "scatter-plot":
        chart_ids = ids_from_scatter(scatter_selection)
        if chart_ids:
            state["selected_ids"] = sorted(base_ids & chart_ids)
    elif ctx.triggered_id == "genre-bar-chart":
        chart_ids = ids_from_genre(genre_click)
        if chart_ids:
            state["selected_ids"] = sorted(base_ids & chart_ids)
    elif ctx.triggered_id == "timeline-chart":
        chart_ids = ids_from_timeline(timeline_selection)
        if chart_ids:
            state["selected_ids"] = sorted(base_ids & chart_ids)
    elif ctx.triggered_id == "rating-histogram":
        chart_ids = ids_from_rating(rating_click)
        if chart_ids:
            state["selected_ids"] = sorted(base_ids & chart_ids)
    elif ctx.triggered_id in {
        "genre-filter",
        "budget-filter",
        "revenue-filter",
        "year-filter",
        "rating-filter",
    }:
        if state["selected_ids"] is not None:
            state["selected_ids"] = sorted(
                set(state["selected_ids"]) & base_ids
            )
    return (
        state,
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
    )


@app.callback(
    Output("scatter-plot", "figure"),
    Output("genre-bar-chart", "figure"),
    Output("timeline-chart", "figure"),
    Output("rating-histogram", "figure"),
    Output("kpi-count", "children"),
    Output("kpi-revenue", "children"),
    Output("kpi-rating", "children"),
    Output("selection-status", "children"),
    Input("filter-store", "data"),
)
def update_dashboard(
    filter_state: dict,
) -> tuple:
    """Redraw all views and KPIs from the current persistent filter state."""
    selected_ids = filter_state.get("selected_ids")
    if selected_ids is None:
        selected = MOVIES[MOVIES["id"].isin(ids_for_controls(filter_state))]
    else:
        selected = MOVIES[MOVIES["id"].isin(selected_ids)]

    average_revenue = selected["revenue_millions"].mean()
    average_rating = selected["vote_average"].mean()
    revenue_text = (
        f"${average_revenue:,.1f}M" if pd.notna(average_revenue) else "N/A"
    )
    rating_text = f"{average_rating:.2f}" if pd.notna(average_rating) else "N/A"

    return (
        scatter_figure(selected),
        genre_figure(selected),
        timeline_figure(selected),
        rating_figure(selected),
        f"{len(selected):,}",
        revenue_text,
        rating_text,
        (
            f"Showing {len(selected):,} movies with complete financial data "
            f"of {MOVIES['id'].nunique():,} released movies "
            f"({MISSING_FINANCIAL_COUNT:,} missing budget or revenue)"
        ),
    )


if __name__ == "__main__":
    app.run(debug=True)
