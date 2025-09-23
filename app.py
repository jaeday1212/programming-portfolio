import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import os
from datetime import date

CSV_PATH = "device_metrics.csv"

if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(
        f"Expected {CSV_PATH} not found. Run device_simulator.py first to generate initial history."
    )

df = pd.read_csv(CSV_PATH)

EXPECTED_COLS = {"date", "device_id", "temperature_c", "humidity_pct", "battery_pct", "error_count", "status"}
missing = EXPECTED_COLS - set(df.columns)
if missing:
    raise ValueError(f"CSV missing expected columns: {missing}")

df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['device_id', 'date'])

DEVICE_IDS = sorted(df['device_id'].unique().tolist())
DEFAULT_DEVICE = DEVICE_IDS[0]
METRICS = [
    {"label": "Temperature (C)", "value": "temperature_c"},
    {"label": "Humidity (%)", "value": "humidity_pct"},
    {"label": "Battery (%)", "value": "battery_pct"},
    {"label": "Error Count", "value": "error_count"},
]
METRIC_META = {
    "temperature_c": {"label": "Temperature (°C)", "unit": "°C", "decimals": 2},
    "humidity_pct": {"label": "Humidity (%)", "unit": "%", "decimals": 1},
    "battery_pct": {"label": "Battery (%)", "unit": "%", "decimals": 1},
    "error_count": {"label": "Error Count", "unit": "", "decimals": 0},
}
STATUS_COLORS = {
    "OK": "#2E8B57",
    "WARN": "#FFA500",
    "ERROR": "#CD5C5C",
    "LOW_BATTERY": "#8B0000",
}

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
    <title>Device Metrics Dashboard</title>
    {%favicon%}
    {%css%}
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&display=swap');
        :root {
            --bg-deep: #030a17;
            --bg: #07111f;
            --bg-alt: #0d1f33;
            --grid-line: rgba(0, 217, 255, 0.08);
            --accent: #16e0ff;
            --accent-glow: 0 0 6px #16e0ff, 0 0 14px #16e0ff99;
            --accent-alt: #ff00aa;
            --text: #e6f6ff;
            --text-dim: #86a2b7;
            --warn: #ffaa33;
            --error: #ff3864;
            --radius: 14px;
            --trans: 260ms cubic-bezier(.2,.8,.2,1);
        }
        body {
            font-family: 'Rajdhani', system-ui, sans-serif;
            background:
                radial-gradient(circle at 20% 15%, #0d2744 0%, transparent 60%),
                radial-gradient(circle at 80% 80%, #101d33 0%, transparent 55%),
                linear-gradient(140deg, var(--bg-deep) 0%, var(--bg) 55%, #06101c 100%);
            color: var(--text);
            line-height: 1.5;
            min-height: 100vh;
            position: relative;
        }
        body:before {
            content:""; position:fixed; inset:0; pointer-events:none;
            background:
              repeating-linear-gradient(90deg, var(--grid-line) 0 1px, transparent 1px 80px),
              repeating-linear-gradient(0deg, var(--grid-line) 0 1px, transparent 1px 80px);
            mask: radial-gradient(circle at center, rgba(255,255,255,.35), transparent 70%);
        }
        .card {
            border-radius: var(--radius);
            background: linear-gradient(155deg, #0b1828 0%, #06111d 60%, #0b1f35 100%);
            border: 1px solid #0f324e;
            box-shadow: 0 4px 18px -4px #000, 0 0 0 1px rgba(22,224,255,0.04);
            position: relative; overflow:hidden;
            transition: transform var(--trans), box-shadow var(--trans), border-color var(--trans);
        }
        .card:before {
            content:""; position:absolute; inset:0; opacity:.18;
            background:
              radial-gradient(circle at 70% 20%, #16e0ff44, transparent 60%),
              radial-gradient(circle at 10% 80%, #ff00aa33, transparent 65%);
            mix-blend-mode:screen; pointer-events:none;
        }
        .card:hover {
            transform: translateY(-6px) scale(1.01);
            border-color: #16e0ffaa;
            box-shadow: var(--accent-glow), 0 10px 34px -8px #000;
        }
        .header-section {
            background: linear-gradient(120deg, #04101d 0%, #06263f 50%, #04101d 100%);
            padding: 36px 32px 42px;
            border-radius: 24px;
            margin-bottom: 32px;
            text-align:center; position:relative; overflow:hidden;
            border: 1px solid #08324a;
            box-shadow: 0 0 0 1px #08324a, 0 0 25px -4px #041827;
        }
        .header-section:after {
            content:""; position:absolute; inset:0; pointer-events:none; opacity:.4;
            background:
              linear-gradient(60deg, transparent 0%, #16e0ff22 40%, transparent 70%),
              radial-gradient(circle at 30% 20%, #16e0ff11, transparent 60%);
        }
        .dashboard-title {
            margin:0; font-weight:700; letter-spacing:3px; font-size: clamp(2rem,3.5vw,3rem);
            background: linear-gradient(90deg,#16e0ff,#9b51ff 40%,#ff00aa 80%);
            -webkit-background-clip:text; color:transparent;
            filter: drop-shadow(0 0 4px #16e0ff99);
            position:relative; padding-bottom:8px;
        }
        .dashboard-title:after {
            content:""; position:absolute; left:50%; bottom:-12px; transform:translateX(-50%);
            width:140px; height:5px; border-radius:4px;
            background: linear-gradient(90deg,transparent,#16e0ff,#ff00aa,transparent);
            box-shadow:0 0 8px #16e0ffcc;
        }
        .dashboard-subtitle { margin-top:20px; font-weight:400; letter-spacing:1px; color: var(--text-dim); }
        .input-label { font-weight:600; margin-bottom:12px; color:var(--accent); letter-spacing:.8px; display:flex; align-items:center; gap:10px; }
        .input-label:before { content:'◇'; color:var(--accent-alt); text-shadow:0 0 6px var(--accent-alt); }
        .chart-title { font-weight:600; text-align:center; padding:18px 10px 10px; letter-spacing:.6px; position:relative; margin-bottom:4px; color:var(--accent); }
        .chart-title:after { content:""; position:absolute; bottom:4px; left:50%; transform:translateX(-50%); width:90px; height:3px; background:linear-gradient(90deg,transparent,var(--accent),var(--accent-alt),transparent); box-shadow:0 0 6px #16e0ff; }
        .summary-text { background: linear-gradient(135deg,#081727,#04101c); padding:18px 20px; border-radius: var(--radius); border:1px solid #0d3b55; box-shadow:0 0 0 1px #0d3b55, 0 0 18px -2px #16e0ff55; }
        .footer { text-align:center; padding:26px 12px; margin-top:40px; font-size:.85rem; opacity:.75; border-top:1px solid #062c42; }
        /* Scrollbars */
        ::-webkit-scrollbar{ width:10px; height:10px; }
        ::-webkit-scrollbar-track{ background:#061522; }
        ::-webkit-scrollbar-thumb{ background:#0d314c; border-radius:20px; }
        ::-webkit-scrollbar-thumb:hover{ background:#16e0ff; box-shadow:0 0 8px #16e0ff; }
        /* Dropdown (react-select) */
    /* CONTROL PANEL (refined) */
    .control-bar{display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:24px; width:100%;}
    .control-card{position:relative; background:#0a1b29; border:1px solid #103449; border-radius:20px; padding:18px 20px 22px; display:flex; flex-direction:column; justify-content:flex-start; min-height:140px; box-shadow:0 4px 18px -6px #000; transition:var(--trans);}  
    .control-card:before{content:""; position:absolute; inset:0; background:radial-gradient(circle at 80% 20%,#16e0ff1c,transparent 70%); opacity:.9; pointer-events:none; mix-blend-mode:screen;}
    .control-card:hover{border-color:#16e0ff; box-shadow:0 0 0 1px #16e0ff,0 8px 30px -10px #16e0ff55;}
    .control-label{font-size:.9rem; font-weight:600; letter-spacing:.7px; margin:0 0 10px; display:flex; align-items:center; gap:8px; color:var(--accent);}
    .control-label .fa{margin-right:2px!important;}
    /* Dropdown (compact) */
    .Select-control{background:#091826!important; border:1px solid #123c59!important; border-radius:14px!important; min-height:50px!important; width:100%!important; box-shadow:none!important; transition:var(--trans);}
    .Select-control:hover{border-color:#16e0ff!important; box-shadow:0 0 0 1px #16e0ff!important;}
    .Select-menu-outer{background:#081a28!important; border:1px solid #123c59!important; border-top:none!important; border-radius:0 0 14px 14px!important; box-shadow:0 10px 30px -8px #000; width:100%!important;}
    .Select-value-label{color:var(--text)!important; font-weight:500;}
    .Select-placeholder{color:#5f7585!important;}
    /* Status pills */
    .status-filter-wrapper{display:flex; flex-wrap:wrap; gap:10px; margin-top:2px;}
    .status-filter-wrapper label{background:#091e2d; padding:6px 12px 7px; border:1px solid #123c59; border-radius:12px; font-size:.75rem; letter-spacing:.5px; cursor:pointer; color:#8aa5b5; transition:var(--trans);} 
    .status-filter-wrapper label:hover{border-color:#16e0ff; color:#16e0ff;}
    .status-filter-wrapper input{display:none;}
    .status-filter-wrapper input:checked + span{color:#16e0ff; text-shadow:0 0 6px #16e0ffaa; font-weight:600;}
    @media (max-width:900px){ .control-card{min-height: unset;} }
    /* Remove inner focus square inside dropdown */
    .Select-control .Select-input input{box-shadow:none!important; outline:none!important; background:transparent!important;}
    .Select-control *:focus{outline:none!important;}
    .Select-control.is-focused{border-color:#16e0ff!important; box-shadow:0 0 0 1px #16e0ff!important;}
        /* Checklist */
        .dash-checklist input{ accent-color:var(--accent); }
        .dash-checklist label{ margin-right:14px; }
        /* Slider */
        .rc-slider-rail{ height:6px!important; background:#0d324d!important; }
        .rc-slider-track{ height:6px!important; background:linear-gradient(90deg,#16e0ff,#ff00aa)!important; box-shadow:0 0 6px #16e0ff; }
        .rc-slider-handle{ width:20px!important; height:20px!important; margin-top:-7px!important; background:#16e0ff!important; border:2px solid #07111d!important; box-shadow:0 0 0 4px #16e0ff55!important; }
        /* Inputs */
        input[type=text]{ background:#081727!important; border:1px solid #0d3b55!important; border-radius:14px!important; padding:14px 18px!important; font-size:1rem; color:var(--text)!important; box-shadow:0 0 0 1px #0d3b55!important; transition:var(--trans); }
        input[type=text]:focus{ border-color:#16e0ff!important; box-shadow:0 0 0 1px #16e0ff,0 0 14px -2px #16e0ff!important; }
        /* Animations */
        @keyframes fadeIn{0%{opacity:0; transform:translateY(18px);}100%{opacity:1; transform:none;}}
        .fade-in{ animation:fadeIn .65s var(--trans); }
        /* Icons */
        .fas,.fa{ margin-right:10px!important; filter:drop-shadow(0 0 4px #16e0ff55); }
        .icon-lg{ margin-right:14px!important; }
        /* Loading */
        ._dash-loading{ background:#081727aa!important; backdrop-filter:blur(6px); border:1px solid #0d3b55; border-radius:var(--radius); }
        /* Graph tweaks */
        .js-plotly-plot .plotly text{ font-family:'Rajdhani',sans-serif!important; }
        /* Utility */
        @media (max-width: 992px){ .Select-control{min-height:60px!important;} }
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
            html.H1([
                html.Span(html.I(className="fas fa-microchip", style={
                    "marginRight":"14px",
                    "color":"#16e0ff",
                    "filter":"drop-shadow(0 0 6px #16e0ff)"
                })),
                "Device Fleet Monitor"
            ], className="dashboard-title"),
            html.P("Tracking synthetic device health & performance (CSV updates daily)",
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
            dbc.Col(
                html.Div([
                    html.Div([
                        html.Div([
                            html.Div([html.I(className="fas fa-hdd"), html.Span("Device:")], className="control-label"),
                            dcc.Dropdown(
                                options=[{"label": f"Device {d}", "value": d} for d in DEVICE_IDS],
                                value=DEFAULT_DEVICE,
                                id="device-select",
                                clearable=False,
                            ),
                        ], className="control-card"),
                        html.Div([
                            html.Div([html.I(className="fas fa-sliders-h"), html.Span("Metric:")], className="control-label"),
                            dcc.Dropdown(
                                options=METRICS,
                                value="temperature_c",
                                id="metric-select",
                                clearable=False,
                            ),
                        ], className="control-card"),
                        html.Div([
                            html.Div([html.I(className="fas fa-filter"), html.Span("Status Filter:")], className="control-label"),
                            dcc.Checklist(
                                options=[{"label": s, "value": s} for s in STATUS_COLORS.keys()],
                                value=list(STATUS_COLORS.keys()),
                                id="status-filter",
                                className="status-filter-wrapper",
                                inputStyle={"display": "none"},
                                labelStyle={"display": "flex", "alignItems": "center"}
                            )
                        ], className="control-card"),
                    ], className="control-bar")
                ]), width=12
            ),
            className="mb-4"
        ),
        # ---------- METRIC TIMESERIES ----------
        dbc.Row([
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.H4([html.I(className="fas fa-chart-line", style={"marginRight": "12px"}),
                                 "Daily Trend (Selected Device)"], className="chart-title"),
                        dcc.Loading(
                            type="circle",
                            color="#e94560",
                            children=dcc.Graph(id="metric-timeseries", config={"displayModeBar": False})
                        )
                    ]), className="card"
                ), width=12, className="fade-in"
            )
        ], className="mb-4"),

        # ---------- BATTERY STATUS OVERVIEW ----------
        dbc.Row([
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.H4([html.I(className="fas fa-battery-half", style={"marginRight": "12px"}),
                                 "Current Battery & Status"], className="chart-title"),
                        dcc.Loading(
                            type="circle",
                            color="#e94560",
                            children=dcc.Graph(id="battery-overview", config={"displayModeBar": False})
                        )
                    ]), className="card"
                ), width=12, className="fade-in"
            )
        ], className="mb-4"),

        # ---------- SUMMARY / LAST UPDATE ----------
        dbc.Row([
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-info-circle", style={"color": "#e94560", "fontSize": "1.2rem", "marginRight": "12px"}),
                            html.Span(id="summary-text", style={"verticalAlign": "middle"})
                        ], className="d-flex align-items-center")
                    ]), className="card"
                ), width=12
            )
        ], className="mb-4"),

        # ---------- FOOTER ----------
        html.Div([
            html.P([
                "Synthetic device metrics demo • CSV appends daily • ",
                html.Span(f"Today: {date.today().isoformat()}")
            ])
        ], className="footer"),
    ],  # close main list
    fluid=True,
    className="px-4 py-4",
)

# --------------------------------------------------
# 4.  CALLBACKS
# --------------------------------------------------
@app.callback(
    Output("metric-timeseries", "figure"),
    [Input("device-select", "value"), Input("metric-select", "value"), Input("status-filter", "value")]
)
def update_metric_timeseries(device_id, metric, statuses):
    device_df = df[df['device_id'] == device_id]
    device_df = device_df[device_df['status'].isin(statuses)]
    if device_df.empty:
        fig = go.Figure()
        fig.update_layout(title="No data for selection", template="plotly_dark")
        return fig
    meta = METRIC_META.get(metric, {"label": metric, "unit": "", "decimals": 2})
    fig = px.line(device_df, x='date', y=metric, title=f"Device {device_id}: {meta['label']} over Time")
    fig.update_traces(mode='lines+markers', marker=dict(size=6))
    # Hover formatting
    decimals = meta['decimals']
    unit = meta['unit']
    hover_tmpl = (
        f"<b>{{{{x|%b %d, %Y}}}}</b><br>{meta['label']}: {{{{y:.{decimals}f}}}}{unit}<extra></extra>"
    )
    fig.update_traces(hovertemplate=hover_tmpl)
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(22, 33, 62, 0.7)",
        paper_bgcolor="rgba(22, 33, 62, 0)",
        font=dict(color="#e6e6e6"),
        height=420,
        margin=dict(t=60, b=50, l=50, r=30)
    )
    # Axis labels + units
    yaxis_title = meta['label']
    if unit and unit not in yaxis_title:
        yaxis_title = f"{yaxis_title}"
    fig.update_yaxes(title=yaxis_title, ticksuffix=(unit if unit in ["%","°C"] else None))
    fig.update_xaxes(tickformat="%b %d", title="Date")
    return fig

@app.callback(
    Output("battery-overview", "figure"),
    [Input("status-filter", "value")]
)
def update_battery_overview(statuses):
    # Get last record per device
    latest = df.sort_values(['device_id','date']).groupby('device_id').tail(1)
    # Ensure we include all known device ids (even if somehow missing data)
    all_devices_df = pd.DataFrame({'device_id': DEVICE_IDS})
    latest = all_devices_df.merge(latest, on='device_id', how='left')
    # Filter by selected statuses (drop rows without status or not selected)
    latest = latest[latest['status'].isin(statuses)]
    if latest.empty:
        fig = go.Figure()
        fig.update_layout(title="No devices match status filter", template="plotly_dark")
        return fig
    latest['device_label'] = latest['device_id'].apply(lambda x: f"Device {x}")
    fig = px.bar(latest, x='device_label', y='battery_pct', color='status', title='Latest Battery Levels by Device',
                 color_discrete_map=STATUS_COLORS, text='battery_pct', category_orders={'device_label': [f"Device {d}" for d in DEVICE_IDS]})
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(22, 33, 62, 0.7)",
        paper_bgcolor="rgba(22, 33, 62, 0)",
        font=dict(color="#e6e6e6"),
        height=420,
        margin=dict(t=60, b=50, l=50, r=30)
    )
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside',
                      hovertemplate="%{x}<br>Battery: %{y:.1f}%<br>Status: %{marker.color}<extra></extra>")
    fig.update_yaxes(title="Battery (%)", ticksuffix="%")
    fig.update_xaxes(title="Device")
    return fig

@app.callback(
    Output("summary-text", "children"),
    [Input("status-filter", "value")]
)
def update_summary(statuses):
    latest = df.sort_values('date').groupby('device_id').tail(1)
    total = len(latest)
    counts = latest['status'].value_counts().to_dict()
    parts = [f"{k}:{counts.get(k,0)}" for k in STATUS_COLORS.keys() if k in statuses]
    last_date = df['date'].max().date().isoformat()
    return f"Devices: {total} • Status breakdown (filtered): {' | '.join(parts)} • Last update day in CSV: {last_date}"


# --------------------------------------------------
# 5.  RUN SERVER
# --------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)