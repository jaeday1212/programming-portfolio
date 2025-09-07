import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
from dash import dash_table
import dash_bootstrap_components as dbc
import base64
import os


if os.path.exists("processed_movies.csv"):
    DATA_PATH = "processed_movies.csv"
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded in data from {DATA_PATH}")
else:
    raise FileNotFoundError("Data file not found.")

df["age_rating"] = df["age_rating"].fillna("Unrated")
df["tone_count"]  = pd.to_numeric(df["tone_count"],  errors="coerce")
df["theme_count"] = pd.to_numeric(df["theme_count"], errors="coerce")
df = df.dropna(subset=["age_rating", "tone_count", "theme_count"])


ALL_RATINGS     = sorted(df["age_rating"].unique().tolist())
DEFAULT_RATINGS = ["PG", "PG-13", "R"]

RATING_COLORS = {
    "G":       "#2E8B57",
    "PG":      "#4682B4",
    "PG-13":   "#9370DB",
    "R":       "#CD5C5C",
    "NC-17":   "#8B0000",
    "Unrated": "#808080",
}

custom_colors = ["#003f5c", "#444e86", "#955196", "#dd5182",
                 "#ff6e54", "#ffa600"]

# --------------------------------------------------
# 2.  DASH APP  &  CUSTOM CSS
# --------------------------------------------------
app = Dash(__name__, external_stylesheets=[dbc.themes.SUPERHERO, 'https://use.fontawesome.com/releases/v5.15.4/css/all.css'])
server = app.server

app.index_string = """
<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>Movie Explorer Dashboard</title>
    {%favicon%}
    {%css%}
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
        
        body {
            background: linear-gradient(135deg, #0f172a 0%, #1a1a2e 100%);
            color: #e6e6e6;
            font-family: 'Poppins', sans-serif;
            line-height: 1.6;
        }
        
        .card {
            border-radius: 12px;
            background: rgba(22, 33, 62, 0.95);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
            margin-bottom: 20px;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            border: 1px solid rgba(83, 52, 131, 0.2);
            overflow: hidden;
        }
        
        .card:hover {
            box-shadow: 0 15px 30px rgba(233, 69, 96, 0.2);
            transform: translateY(-8px) scale(1.01);
        }
        
        .header-section {
            background: linear-gradient(135deg, #0f3460 0%, #533483 100%);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 25px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            position: relative;
            overflow: hidden;
        }
        
        .header-section:before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><rect fill="none" width="50" height="50" stroke="rgba(255,255,255,0.1)" stroke-width="1"/></svg>') repeat;
            opacity: 0.2;
        }
        
        .dashboard-title {
            font-weight: 700;
            letter-spacing: 2px;
            color: #e94560;
            text-shadow: 3px 3px 6px rgba(0,0,0,0.6);
            margin: 0;
            font-size: 2.5rem;
            position: relative;
            display: inline-block;
        }
        
        .dashboard-title:after {
            content: '';
            position: absolute;
            bottom: -10px;
            left: 50%;
            transform: translateX(-50%);
            width: 80px;
            height: 4px;
            background: linear-gradient(90deg, transparent, rgba(233, 69, 96, 0.8), transparent);
        }
        
        .dashboard-subtitle {
            opacity: 0.9;
            margin: 20px 0 5px;
            font-weight: 300;
            letter-spacing: 1px;
            font-size: 1.1rem;
        }
        
        .input-label {
            font-weight: 600;
            margin-bottom: 10px;
            color: #e94560;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
        }
        
        .input-label:before {
            content: '⟡';
            margin-right: 8px;
            color: #e94560;
            font-size: 14px;
        }
        
        .chart-title {
            font-weight: 600;
            text-align: center;
            padding: 15px 10px;
            color: #e94560;
            letter-spacing: 0.5px;
            position: relative;
            margin-bottom: 10px;
        }
        
        .chart-title:after {
            content: "";
            position: absolute;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 60px;
            height: 3px;
            background: linear-gradient(90deg, transparent, #e94560, transparent);
        }
        
        .summary-text {
            background: rgba(22, 33, 62, 0.7);
            padding: 15px;
            border-radius: 8px;
            border-left: 5px solid #e94560;
            font-weight: 300;
            line-height: 1.6;
            backdrop-filter: blur(10px);
        }
        
        .footer {
            text-align: center;
            padding: 25px;
            margin-top: 30px;
            font-size: 0.85rem;
            opacity: 0.7;
            border-top: 1px solid rgba(233, 69, 96, 0.3);
        }
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: #16213e;
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #533483;
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #e94560;
        }
        
        /* Dropdown styling */
        .Select-control {
            background-color: rgba(22, 33, 62, 0.8) !important;
            border-color: #533483 !important;
            border-radius: 8px !important;
            transition: all 0.3s ease;
        }
        
        .Select-control:hover {
            border-color: #e94560 !important;
            box-shadow: 0 0 0 1px #e94560 !important;
        }
        
        .Select-menu-outer {
            background-color: rgba(22, 33, 62, 0.9) !important;
            border-radius: 0 0 8px 8px !important;
            border: 1px solid #533483 !important;
        }
        
        .Select-value-label {
            color: #e6e6e6 !important;
        }
        
        /* Slider styling */
        .rc-slider-track {
            background-color: #e94560 !important;
            height: 4px !important;
        }
        
        .rc-slider-rail {
            height: 4px !important;
            background-color: rgba(83, 52, 131, 0.5) !important;
        }
        
        .rc-slider-handle {
            border-color: #e94560 !important;
            background-color: #e94560 !important;
            box-shadow: 0 0 5px rgba(233, 69, 96, 0.5) !important;
        }
        
        .rc-slider-dot-active {
            border-color: #e94560 !important;
        }
        
        /* Table styling improvements */
        .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner table {
            border-collapse: separate;
            border-spacing: 0;
            border-radius: 8px;
            overflow: hidden;
        }
        
        /* Animation */
        @keyframes fadeIn { 0% { opacity: 0; transform: translateY(20px); } 100% { opacity: 1; transform: translateY(0); } }
        .fade-in { animation: fadeIn 0.6s ease-out; }
        
        /* Card body padding */
        .card-body {
            padding: 1.5rem;
        }
        
        /* Input styling */
        input[type="text"] {
            background-color: rgba(22, 33, 62, 0.7) !important;
            border: 1px solid #533483 !important;
            border-radius: 8px !important;
            padding: 10px 15px !important;
            color: #e6e6e6 !important;
            transition: all 0.3s ease;
        }
        
        input[type="text"]:focus {
            border-color: #e94560 !important;
            box-shadow: 0 0 0 2px rgba(233, 69, 96, 0.25) !important;
            outline: none;
        }
        
        /* Info card styling */
        .info-card {
            background: linear-gradient(135deg, rgba(22, 33, 62, 0.9), rgba(15, 52, 96, 0.9));
            border-left: 5px solid #e94560;
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
        }
        
        /* Loading spinner */
        ._dash-loading {
            background-color: rgba(15, 52, 96, 0.7) !important;
            border-radius: 10px;
            backdrop-filter: blur(5px);
        }
        
        /* Radio buttons */
        .dash-radio {
            background: rgba(22, 33, 62, 0.7);
            border-radius: 8px;
            padding: 8px 15px;
        }
        
        /* Icon spacing */
        .fas, .fa {
            margin-right: 10px !important;
        }
        
        .icon-sm {
            margin-right: 6px !important;
        }
        
        .icon-lg {
            margin-right: 14px !important;
        }
    </style>
</head>
<body>
    {%app_entry%}
    <footer>
        {%config%}
        {%scripts%}
        {%renderer%}
    </footer>
</body>
</html>
"""
app.layout = dbc.Container(
    [
        # ---------- HEADER ----------
        dbc.Row(
            dbc.Col(
                html.Div(
                    [
                        html.H1([html.I(className="fas fa-film icon-lg"), " CINEMATIC EXPLORER"],
                                className="dashboard-title"),
                        html.P("Discover patterns in movie themes, tones, and ratings",
                               className="dashboard-subtitle"),
                    ],
                    className="header-section",
                ),
                width=12,
            ),
            className="mb-4",
        ),

        # ---------- CONTROL PANEL ----------
        dbc.Row(
            [
                # rating filter
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Label([html.I(className="fas fa-filter", style={"marginRight": "12px"}), "Filter by Age Rating:"],
                                           className="input-label"),
                                dcc.Dropdown(
                                    options=[{"label": r, "value": r}
                                             for r in ALL_RATINGS],
                                    value=DEFAULT_RATINGS,
                                    multi=True,
                                    id="select-ratings",
                                    clearable=False,
                                ),
                            ]
                        ),
                        className="card h-100",
                    ),
                    width=4,
                ),

                # chart type
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Label([html.I(className="fas fa-chart-bar", style={"marginRight": "12px"}), "Top Chart Type:"],
                                           className="input-label"),
                                dcc.RadioItems(
                                    options=[{"label": "Top Tones", "value": "tone"},
                                             {"label": "Top Themes", "value": "theme"}],
                                    value="tone",
                                    id="top-type-toggle",
                                    inline=True,
                                    inputStyle={"margin-right": "12px"},
                                    style={"display": "flex",
                                           "justifyContent": "space-evenly",
                                           "paddingTop": "10px",
                                           "paddingBottom": "5px"},
                                    className="dash-radio"
                                ),
                            ]
                        ),
                        className="card h-100",
                    ),
                    width=4,
                ),

                # search
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Label([html.I(className="fas fa-search", style={"marginRight": "12px"}), "Search by Movie Title:"],
                                           className="input-label"),
                                dcc.Input(
                                    id="search-title",
                                    type="text",
                                    placeholder="Enter keyword...",
                                    debounce=True,
                                    style={"width": "100%"},
                                ),
                            ]
                        ),
                        className="card h-100",
                    ),
                    width=4,
                ),
            ],
            className="mb-4",
        ),

        # ---------- CHARTS ----------
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H4([html.I(className="fas fa-chart-pie", style={"marginRight": "12px"}), "Age Rating Distribution"],
                                    className="chart-title"),
                            dcc.Loading(
                                type="circle",
                                color="#e94560",
                                children=dcc.Graph(
                                    id="rating_bar_chart",
                                    config={"displayModeBar": False},
                                ),
                            ),
                        ]
                    ),
                    className="card",
                ),
                width=12,
                className="fade-in",
            ),
            className="mb-4",
        ),

        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H4([html.I(className="fas fa-trophy", style={"marginRight": "12px"}), "Top Movie Elements by Rating"],
                                    className="chart-title"),
                            dcc.Loading(
                                type="circle",
                                color="#e94560",
                                children=dcc.Graph(
                                    id="top_bar_chart",
                                    config={"displayModeBar": False},
                                ),
                            ),
                        ]
                    ),
                    className="card",
                ),
                width=12,
                className="fade-in",
            ),
            className="mb-4",
        ),

        # Interpretation Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H5([html.I(className="fas fa-lightbulb", style={"marginRight": "12px"}), "Content Strategy Insights"], 
                                style={"color": "#e94560", "marginBottom": "15px", "fontWeight": "bold", 
                                      "borderBottom": "2px solid rgba(233, 69, 96, 0.3)", "paddingBottom": "8px"}),
                            html.P([
                                html.Strong("Tones match audience expectations: "), 
                                "R-rated films focus on suspense for adults, while PG/PG-13 prioritize hopeful narratives for younger viewers."
                            ], style={"fontSize": "0.95rem", "marginBottom": "12px"}),
                            html.P([
                                html.Strong("Themes align with viewer maturity: "), 
                                "R-rated explores complex relationships, PG-13 centers on identity, and G/PG emphasizes simple life lessons."
                            ], style={"fontSize": "0.95rem", "marginBottom": "0"})
                        ])
                    ])
                ], className="card info-card")
            ], width=12)
        ], className="mb-4"),

        # ---------- SUMMARY ----------
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-info-circle", style={"color": "#e94560", "fontSize": "1.2rem", "marginRight": "12px"}),
                            html.Span(id="summary-text", style={"verticalAlign": "middle"})
                        ], className="d-flex align-items-center")
                    ]),
                    className="card",
                ),
                width=12,
            ),
            className="mb-4",
        ),

        # ---------- ROW SLIDER ----------
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.Label([html.I(className="fas fa-list-ol", style={"marginRight": "12px"}), "Number of Movies to Display:"],
                                       className="input-label"),
                            dcc.Slider(
                                min=5,
                                max=25,
                                step=5,
                                value=10,
                                marks={i: str(i) for i in range(5, 30, 5)},
                                id="row-slider",
                            ),
                        ]
                    ),
                    className="card",
                ),
                width=12,
            ),
            className="mb-4",
        ),

        # ---------- MOVIE TABLE ----------
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H4([html.I(className="fas fa-film", style={"marginRight": "12px"}), "Filtered Movie Collection"],
                                    className="chart-title"),
                            dcc.Loading(
                                type="circle",
                                color="#e94560",
                                children=dash_table.DataTable(
                                    id="movie-table",
                                    columns=[
                                        {"name": "Movie Title", "id": "movie_title"},
                                        {"name": "Age Rating", "id": "age_rating"},
                                        {"name": "Tones", "id": "tone_str"},
                                        {"name": "Themes", "id": "themes_str"},
                                    ],
                                    style_table={"overflowX": "auto"},
                                    style_cell={
                                        "textAlign": "left", 
                                        "whiteSpace": "normal",
                                        "backgroundColor": "rgba(22, 33, 62, 0.9)",
                                        "color": "#e6e6e6",
                                        "border": "1px solid rgba(83, 52, 131, 0.5)",
                                        "padding": "12px 15px",
                                        "fontSize": "13px",
                                    },
                                    style_header={
                                        "backgroundColor": "rgba(15, 52, 96, 0.95)",
                                        "fontWeight": "bold",
                                        "color": "#e6e6e6",
                                        "border": "1px solid rgba(83, 52, 131, 0.5)",
                                        "padding": "12px 15px",
                                    },
                                    style_data_conditional=[
                                        {
                                            "if": {"row_index": "odd"},
                                            "backgroundColor": "rgba(28, 39, 76, 0.9)"
                                        },
                                        {
                                            "if": {"column_id": "movie_title"},
                                            "fontWeight": "bold",
                                            "color": "#e94560"
                                        }
                                    ],
                                    page_size=10,
                                ),
                            ),
                        ]
                    ),
                    className="card",
                ),
                width=12,
            ),
            className="mb-4",
        ),

        # ---------- FOOTER ----------
        html.Div([
            html.P([
                "Created with ", 
                html.I(className="fas fa-heart", style={"color": "#e94560", "margin": "0 6px"}), 
                " using Dash and Plotly • Movie data analysis project • ",
                html.I(className="fas fa-code", style={"margin": "0 6px"}), 
                " with ", 
                html.I(className="fas fa-coffee", style={"margin": "0 6px"})
            ])
        ], className="footer"),
    ],
    fluid=True,
    className="px-4 py-4",
)

# --------------------------------------------------
# 4.  CALLBACKS
# --------------------------------------------------
# ------------ 4A.  TOP MOVIE ELEMENTS -------------
@app.callback(
    Output("top_bar_chart", "figure"),
    [
        Input("select-ratings", "value"),
        Input("top-type-toggle", "value"),
        Input("search-title", "value"),
    ],
)
def update_top_chart(selected_ratings, top_type, search_query):

    # empty selection → return blank fig
    if not selected_ratings:
        blank = go.Figure()
        blank.update_layout(
            title="Top Tones or Themes by Rating (No selection)",
            template="plotly_dark",
            plot_bgcolor="rgba(22, 33, 62, 0.7)",
            paper_bgcolor="rgba(22, 33, 62, 0)",
            font=dict(color="#e6e6e6"),
            margin=dict(t=50, b=30, l=40, r=40),
            height=450,
        )
        return blank

    # filter rows
    filtered = df[df["age_rating"].isin(selected_ratings)]
    if search_query:
        filtered = filtered[
            filtered["movie_title"]
            .str.contains(search_query, case=False, na=False)
        ]

    col = "tone_str" if top_type == "tone" else "themes_str"

    # explode tones/themes safely
    item_rows = []
    for _, row in filtered.iterrows():
        raw = row.get(col)
        if pd.notna(raw) and str(raw).strip():
            items = [
                i.strip() for i in str(raw).split(",")
                if i.strip() and i.lower() != "nan"
            ]
            for item in items:
                item_rows.append(
                    {"age_rating": row["age_rating"], "label": item}
                )

    item_df = pd.DataFrame(item_rows)
    if item_df.empty:
        nodata = go.Figure()
        nodata.update_layout(
            title="No data available with current filters",
            template="plotly_dark",
            plot_bgcolor="rgba(22, 33, 62, 0.7)",
            paper_bgcolor="rgba(22, 33, 62, 0)",
            font=dict(color="#e6e6e6"),
            margin=dict(t=50, b=30, l=40, r=40),
            height=450,
        )
        return nodata

    # take *top one* per rating
    top_items = (
        item_df.groupby(["age_rating", "label"])
        .size()
        .reset_index(name="count")
        .sort_values(["age_rating", "count"], ascending=[True, False])
        .groupby("age_rating")
        .head(1)
    )

    fig = px.bar(
        top_items,
        x="count",
        y="label",
        color="age_rating",
        orientation="h",
        title=f"Top {top_type.capitalize()} by Rating",
        text="count",
        color_discrete_map=RATING_COLORS,
        category_orders={"age_rating": sorted(selected_ratings)},
    )

    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(22, 33, 62, 0.7)",
        paper_bgcolor="rgba(22, 33, 62, 0)",
        font=dict(color="#e6e6e6", family="Poppins"),
        title_font=dict(size=22, color="#e94560", family="Poppins"),
        legend_title_font=dict(size=12, color="#e6e6e6", family="Poppins"),
        legend_font=dict(size=10, color="#e6e6e6", family="Poppins"),
        xaxis=dict(
            title="Count", 
            color="#e6e6e6", 
            gridcolor="rgba(83, 52, 131, 0.3)",
            linecolor="rgba(83, 52, 131, 0.5)",
            zeroline=False,
        ),
        yaxis=dict(
            title=top_type.capitalize(), 
            color="#e6e6e6", 
            gridcolor="rgba(83, 52, 131, 0.3)",
            linecolor="rgba(83, 52, 131, 0.5)",
        ),
        margin=dict(t=50, b=30, l=40, r=40),
        height=450,
        bargap=0.2,
        showlegend=True,
    )

    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>Count: %{x}"
        "<br>Rating: %{marker.color}<extra></extra>",
        textposition="outside",
        opacity=0.9,
        textfont=dict(family="Poppins", color="white", size=12),
    )

    # proper y‑axis ordering
    fig.update_yaxes(categoryorder="total ascending")
    
    return fig


# ------------ 4B.  AGE‑RATING DISTRIBUTION -------
@app.callback(
    Output("rating_bar_chart", "figure"),
    [Input("select-ratings", "value"), Input("search-title", "value")],
)
def update_rating_bar(selected_ratings, search_query):

    if not selected_ratings:
        blank = go.Figure()
        blank.update_layout(
            title="Number of Movies by Age Rating (No selection)",
            template="plotly_dark",
            plot_bgcolor="rgba(22, 33, 62, 0.7)",
            paper_bgcolor="rgba(22, 33, 62, 0)",
            font=dict(color="#e6e6e6"),
            margin=dict(t=50, b=30, l=40, r=40),
            height=450,
        )
        return blank

    filtered = df[df["age_rating"].isin(selected_ratings)]
    if search_query:
        filtered = filtered[
            filtered["movie_title"]
            .str.contains(search_query, case=False, na=False)
        ]

    # This is the key fix - using the approach that works in the second implementation
    counts = filtered["age_rating"].value_counts().reset_index()
    counts.columns = ["age_rating", "count"]  # Explicitly set column names

    fig = px.bar(
        counts,
        x="age_rating",
        y="count",
        color="age_rating",
        title="Number of Movies by Age Rating",
        text="count",
        color_discrete_map=RATING_COLORS,
    )

    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(22, 33, 62, 0.7)",
        paper_bgcolor="rgba(22, 33, 62, 0)",
        font=dict(color="#e6e6e6", family="Poppins"),
        title_font=dict(size=22, color="#e94560", family="Poppins"),
        legend_title_font=dict(size=12, color="#e6e6e6", family="Poppins"),
        legend_font=dict(size=10, color="#e6e6e6", family="Poppins"),
        xaxis=dict(
            title="Age Rating", 
            color="#e6e6e6", 
            gridcolor="rgba(83, 52, 131, 0.3)",
            linecolor="rgba(83, 52, 131, 0.5)",
            zeroline=False,
        ),
        yaxis=dict(
            title="Number of Movies", 
            color="#e6e6e6", 
            gridcolor="rgba(83, 52, 131, 0.3)",
            linecolor="rgba(83, 52, 131, 0.5)",
        ),
        margin=dict(t=50, b=30, l=40, r=40),
        height=450,
        bargap=0.2,
    )

    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>Movies: %{y}<extra></extra>",
        textposition="outside",
        opacity=0.85,
        textfont=dict(family="Poppins", color="white", size=12),
    )

    # add text annotations
    for _, row in counts.iterrows():
        fig.add_annotation(
            x=row["age_rating"],
            y=row["count"],
            text=str(row["count"]),
            showarrow=False,
            font=dict(color="white", family="Poppins", size=14),
            yshift=10,
        )
    return fig

# ------------ 4C.  MOVIE TABLE & SUMMARY ----------
@app.callback(
    [Output("movie-table", "data"), Output("summary-text", "children")],
    [
        Input("select-ratings", "value"),
        Input("search-title", "value"),
        Input("row-slider", "value"),
    ],
)
def update_table_and_summary(selected_ratings, search_query, row_count):
    # Filter based on selected ratings
    filtered = df[df["age_rating"].isin(selected_ratings)]
    
    # Further filter by search query if provided
    if search_query:
        filtered = filtered[
            filtered["movie_title"]
            .str.contains(search_query, case=False, na=False)
        ]
    
    # Sort and limit rows
    filtered = filtered.sort_values("movie_title").head(row_count)
    
    # Create summary message
    summary = (
        f"Showing {len(filtered)} movie(s) with rating(s): "
        f"{', '.join(selected_ratings)}."
    )
    if search_query:
        summary += f" Filtered by keyword: '{search_query}'."
    
    return filtered.to_dict("records"), summary


# --------------------------------------------------
# 5.  RUN SERVER
# --------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)