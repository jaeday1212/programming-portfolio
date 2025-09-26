import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import os
import time
from functools import lru_cache
from datetime import date

CSV_PATH = "device_metrics.csv"

if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(
        f"Expected {CSV_PATH} not found. Run device_simulator.py first to generate initial history."
    )

_initial_df = pd.read_csv(CSV_PATH)
EXPECTED_COLS = {"date", "device_id", "temperature_c", "humidity_pct", "battery_pct", "error_count", "status"}
missing = EXPECTED_COLS - set(_initial_df.columns)
if missing:
    raise ValueError(f"CSV missing expected columns: {missing}")

_initial_df['date'] = pd.to_datetime(_initial_df['date'])
_initial_df = _initial_df.sort_values(['device_id', 'date'])

DEVICE_IDS = sorted(_initial_df['device_id'].unique().tolist())
DEFAULT_DEVICE = DEVICE_IDS[0]

CACHE_TTL = 30  # seconds

@lru_cache(maxsize=1)
def _cached_load(ts_bucket: int):  # ts_bucket changes every CACHE_TTL seconds
    df = pd.read_csv(CSV_PATH)
    # Basic schema guard (silent skip if already validated)
    if EXPECTED_COLS - set(df.columns):
        return _initial_df
    df['date'] = pd.to_datetime(df['date'])
    return df.sort_values(['device_id', 'date'])

def load_dataframe():
    ts_bucket = int(time.time() // CACHE_TTL)
    return _cached_load(ts_bucket)
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
    "OK": "#10b981",        # Success color - meets WCAG AA contrast
    "WARN": "#f59e0b",      # Warning color - meets WCAG AA contrast  
    "ERROR": "#ef4444",     # Error color - meets WCAG AA contrast
    "LOW_BATTERY": "#3b82f6",  # Info color - meets WCAG AA contrast
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
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        :root {
            /* === DESIGN TOKENS === */
            
            /* Spacing Scale (8pt grid) */
            --space-1: 4px;
            --space-2: 8px;
            --space-3: 12px;
            --space-4: 16px;
            --space-6: 24px;
            --space-8: 32px;
            --space-12: 48px;
            --space-16: 64px;
            
            /* Layout */
            --content-max-width: 1280px;
            --page-padding: var(--space-8);
            --section-padding: var(--space-8);
            --card-gap: var(--space-6);
            
            /* Hit Targets */
            --hit-target-min: 48px;
            --hit-target-spacing: var(--space-2);
            
            /* Typography Scale (1.25 ratio) */
            --font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            --font-size-sm: 0.8rem;     /* 12.8px */
            --font-size-base: 1rem;     /* 16px */
            --font-size-lg: 1.125rem;   /* 18px */
            --font-size-xl: 1.25rem;    /* 20px */
            --font-size-2xl: 1.563rem;  /* 25px */
            --font-size-3xl: 1.953rem;  /* 31px */
            --font-size-4xl: 2.441rem;  /* 39px */
            --font-size-5xl: 3.052rem;  /* 49px */
            
            --line-height-tight: 1.25;
            --line-height-base: 1.5;
            --line-height-loose: 1.75;
            
            /* Color System (WCAG AA+ compliant) */
            --color-bg-primary: #0a0f1c;
            --color-bg-secondary: #111827;
            --color-bg-tertiary: #1f2937;
            --color-surface: #374151;
            --color-surface-hover: #4b5563;
            
            --color-text-primary: #f9fafb;    /* 18.05:1 contrast */
            --color-text-secondary: #d1d5db;  /* 12.63:1 contrast */
            --color-text-tertiary: #9ca3af;   /* 7.06:1 contrast */
            --color-text-disabled: #6b7280;   /* 4.54:1 contrast */
            
            --color-primary: #3b82f6;          /* Primary action */
            --color-primary-hover: #2563eb;
            --color-primary-light: #60a5fa;
            
            --color-accent: #06b6d4;           /* Data visualization */
            --color-accent-alt: #8b5cf6;
            
            /* Status Colors (accessible) */
            --color-success: #10b981;          /* OK status */
            --color-success-bg: #065f46;
            --color-warning: #f59e0b;          /* WARN status */
            --color-warning-bg: #92400e;
            --color-error: #ef4444;            /* ERROR status */
            --color-error-bg: #991b1b;
            --color-info: #3b82f6;             /* LOW_BATTERY status */
            --color-info-bg: #1e3a8a;
            
            /* Focus Indicators (WCAG 2.2) */
            --focus-ring: 2px solid var(--color-primary);
            --focus-ring-offset: 2px;
            --focus-contrast-ratio: 3.14; /* Meets WCAG 2.2 */
            
            /* Component Tokens */
            --border-radius-sm: 6px;
            --border-radius-base: 12px;
            --border-radius-lg: 16px;
            --border-radius-full: 9999px;
            
            --border-width: 1px;
            --border-color: rgba(156, 163, 175, 0.2);
            --border-color-hover: rgba(156, 163, 175, 0.4);
            
            /* Shadows */
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-base: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
            
            /* Motion */
            --duration-fast: 150ms;
            --duration-base: 200ms;
            --duration-slow: 300ms;
            --easing: cubic-bezier(0.2, 0.8, 0.2, 1);
            
            /* Grid Breakpoints */
            --breakpoint-sm: 640px;
            --breakpoint-md: 768px;
            --breakpoint-lg: 1024px;
            --breakpoint-xl: 1280px;
        }
        
        /* === BASE STYLES === */
        * {
            box-sizing: border-box;
        }
        
        body {
            font-family: var(--font-family);
            font-size: var(--font-size-base);
            line-height: var(--line-height-base);
            background: 
                radial-gradient(circle at 20% 15%, #1e293b 0%, transparent 60%),
                radial-gradient(circle at 80% 80%, #334155 0%, transparent 55%),
                linear-gradient(140deg, var(--color-bg-primary) 0%, var(--color-bg-secondary) 55%, var(--color-bg-primary) 100%);
            color: var(--color-text-primary);
            min-height: 100vh;
            margin: 0;
            padding: 0;
        }
        
        /* Respect user motion preferences */
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
                scroll-behavior: auto !important;
            }
        }
        
        /* === LAYOUT SYSTEM === */
        .container-fluid {
            max-width: var(--content-max-width);
            margin: 0 auto;
            padding-left: var(--page-padding);
            padding-right: var(--page-padding);
        }
        
        /* Grid Background (subtle) */
        body::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            background:
                repeating-linear-gradient(
                    90deg,
                    rgba(156, 163, 175, 0.03) 0 1px,
                    transparent 1px var(--space-16)
                ),
                repeating-linear-gradient(
                    0deg,
                    rgba(156, 163, 175, 0.03) 0 1px,
                    transparent 1px var(--space-16)
                );
            mask: radial-gradient(circle at center, rgba(255,255,255,0.2), transparent 70%);
        }
        
        /* === COMPONENT SYSTEM === */
        
        /* Cards */
        .card {
            background: var(--color-bg-secondary);
            border: var(--border-width) solid var(--border-color);
            border-radius: var(--border-radius-lg);
            box-shadow: var(--shadow-base);
            transition: all var(--duration-base) var(--easing);
            position: relative;
            overflow: hidden;
        }
        
        .card:hover {
            border-color: var(--border-color-hover);
            box-shadow: var(--shadow-lg);
            transform: translateY(-2px);
        }
        
        .card-body {
            padding: var(--space-6);
        }
        
        /* KPI Cards */
        .kpi {
            background: linear-gradient(150deg, var(--color-bg-tertiary) 0%, var(--color-bg-secondary) 70%);
            text-align: center;
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        
        .kpi-label {
            font-size: var(--font-size-sm);
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: var(--color-text-secondary);
            margin-bottom: var(--space-2);
            line-height: var(--line-height-tight);
        }
        
        .kpi-value {
            font-size: var(--font-size-3xl);
            font-weight: 700;
            color: var(--color-primary-light);
            line-height: var(--line-height-tight);
        }
        
        /* Header Section */
        .header-section {
            background: linear-gradient(120deg, var(--color-bg-secondary) 0%, var(--color-bg-tertiary) 50%, var(--color-bg-secondary) 100%);
            padding: var(--space-12) var(--space-8);
            border-radius: var(--border-radius-lg);
            margin-bottom: var(--space-8);
            text-align: center;
            border: var(--border-width) solid var(--border-color);
            box-shadow: var(--shadow-base);
        }
        
        .dashboard-title {
            margin: 0;
            font-weight: 700;
            font-size: clamp(var(--font-size-3xl), 3.5vw, var(--font-size-5xl));
            letter-spacing: -0.025em;
            color: var(--color-text-primary);
            line-height: var(--line-height-tight);
            margin-bottom: var(--space-2);
        }
        
        .dashboard-title .fa {
            color: var(--color-primary);
            margin-right: var(--space-3);
        }
        
        .dashboard-subtitle {
            font-size: var(--font-size-lg);
            color: var(--color-text-secondary);
            margin: 0;
            font-weight: 400;
        }
        
        /* === INTERACTIVE COMPONENTS === */
        
        /* Control Panel */
        .control-bar {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: var(--card-gap);
            width: 100%;
        }
        
        .control-card {
            background: var(--color-bg-secondary);
            border: var(--border-width) solid var(--border-color);
            border-radius: var(--border-radius-lg);
            padding: var(--space-6);
            box-shadow: var(--shadow-base);
            transition: all var(--duration-base) var(--easing);
            min-height: var(--hit-target-min);
        }
        
        .control-card:hover {
            border-color: var(--border-color-hover);
            box-shadow: var(--shadow-lg);
        }
        
        .control-label {
            font-size: var(--font-size-base);
            font-weight: 600;
            color: var(--color-text-primary);
            margin-bottom: var(--space-3);
            display: flex;
            align-items: center;
            gap: var(--space-2);
        }
        
        .control-label .fa {
            color: var(--color-primary);
            width: 16px; /* Consistent icon width */
        }
        
        /* Form Controls - Accessible Focus */
        .Select-control, 
        input[type="text"],
        input[type="search"] {
            background: var(--color-bg-tertiary) !important;
            border: var(--border-width) solid var(--border-color) !important;
            border-radius: var(--border-radius-base) !important;
            min-height: var(--hit-target-min) !important;
            padding: var(--space-3) var(--space-4) !important;
            color: var(--color-text-primary) !important;
            font-size: var(--font-size-base) !important;
            font-family: var(--font-family) !important;
            transition: all var(--duration-base) var(--easing) !important;
            box-shadow: none !important;
        }

        .Select-control {
            display: inline-flex !important;
            align-items: center !important;
            gap: var(--space-3) !important;
            border-radius: var(--border-radius-full) !important;
            padding: 0 var(--space-4) !important;
            cursor: pointer !important;
            transition: background var(--duration-base) var(--easing) !important;
        }

        .Select-control .Select-value,
        .Select-control .Select-placeholder {
            display: inline-flex !important;
            align-items: center !important;
            line-height: 1 !important;
            flex: 1 1 auto !important;
            justify-content: center !important;
            text-align: center !important;
            width: 100% !important;
        }

        .Select-control .Select-value-label {
            font-weight: 600 !important;
            letter-spacing: 0.01em !important;
            width: 100% !important;
            text-align: center !important;
        }

        .Select-control .Select-input > input {
            color: var(--color-text-primary) !important;
            padding: 0 !important;
        }

        .Select-control .Select-arrow-zone {
            margin-left: auto !important;
            padding: 0 !important;
            display: inline-flex !important;
            align-items: center !important;
        }

        .Select-control .Select-arrow {
            border-top-color: var(--color-text-secondary) !important;
            transition: transform var(--duration-base) var(--easing) !important;
        }

        .is-open > .Select-control .Select-arrow {
            transform: rotate(180deg) !important;
        }

        .is-open > .Select-control {
            border-color: var(--color-primary) !important;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.35) inset !important;
        }
        
        .Select-control:hover,
        input[type="text"]:hover,
        input[type="search"]:hover {
            border-color: var(--border-color-hover) !important;
            background: var(--color-bg-tertiary) !important;
        }
        
        .Select-control:focus,
        .Select-control.is-focused,
        input[type="text"]:focus,
        input[type="search"]:focus {
            outline: var(--focus-ring) !important;
            outline-offset: var(--focus-ring-offset) !important;
            border-color: var(--color-primary) !important;
        }
        
        .Select-value-label {
            color: var(--color-text-primary) !important;
        }
        
        .Select-placeholder {
            color: var(--color-text-tertiary) !important;
            font-weight: 500 !important;
        }
        
        .Select-menu-outer {
            background: var(--color-bg-tertiary) !important;
            border: var(--border-width) solid var(--border-color) !important;
            border-radius: var(--border-radius-base) !important;
            box-shadow: var(--shadow-lg) !important;
            z-index: 1000 !important;
            margin-top: var(--space-2) !important;
        }
        
        .Select-option {
            background: transparent !important;
            color: var(--color-text-primary) !important;
            padding: var(--space-3) var(--space-4) !important;
            border: none !important;
        }

        .Select-option:first-of-type {
            border-top-left-radius: var(--border-radius-base) !important;
            border-top-right-radius: var(--border-radius-base) !important;
        }

        .Select-option:last-of-type {
            border-bottom-left-radius: var(--border-radius-base) !important;
            border-bottom-right-radius: var(--border-radius-base) !important;
        }
        
        .Select-option:hover,
        .Select-option.is-focused {
            background: var(--color-surface) !important;
            color: var(--color-text-primary) !important;
        }
        
        /* Status Filter Chips */
        .status-filter-wrapper {
            display: flex;
            flex-wrap: wrap;
            gap: var(--space-3);
            margin-top: var(--space-1);
        }
        
        .status-filter-wrapper label {
            position: relative;
            background: var(--color-bg-tertiary);
            border: var(--border-width) solid var(--border-color);
            border-radius: var(--border-radius-full);
            padding: 0 var(--space-4);
            font-size: var(--font-size-sm);
            font-weight: 500;
            color: var(--color-text-secondary);
            cursor: pointer;
            transition: all var(--duration-base) var(--easing);
            height: var(--hit-target-min);
            min-width: 88px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            line-height: 1;
            user-select: none;
            box-sizing: border-box;
        }
        
        .status-filter-wrapper label span {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 100%;
        }
        
        /* === CHART & DATA VISUALIZATION === */
        
        .chart-title {
            font-weight: 600;
            font-size: var(--font-size-xl);
            text-align: center;
            color: var(--color-text-primary);
            margin-bottom: var(--space-4);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: var(--space-2);
        }
        
        .chart-title .fa {
            color: var(--color-primary);
        }
        
        /* Chart containers */
        .js-plotly-plot .plotly {
            font-family: var(--font-family) !important;
        }
        
        .js-plotly-plot .plotly .xtick text,
        .js-plotly-plot .plotly .ytick text {
            font-size: var(--font-size-sm) !important;
            fill: var(--color-text-tertiary) !important;
        }
        
        .js-plotly-plot .plotly .xaxislayer-above,
        .js-plotly-plot .plotly .yaxislayer-above {
            opacity: 0.3;
        }
        
        /* === UTILITY CLASSES === */
        
        .summary-text {
            background: var(--color-bg-tertiary);
            border: var(--border-width) solid var(--border-color);
            border-radius: var(--border-radius-base);
            padding: var(--space-4) var(--space-6);
            font-size: var(--font-size-base);
            color: var(--color-text-secondary);
        }
        
        .footer {
            text-align: center;
            padding: var(--space-8) var(--space-4);
            margin-top: var(--space-12);
            font-size: var(--font-size-sm);
            color: var(--color-text-tertiary);
            border-top: var(--border-width) solid var(--border-color);
        }
        
        /* Loading States */
        ._dash-loading {
            background: var(--color-bg-secondary) !important;
            border: var(--border-width) solid var(--border-color) !important;
            border-radius: var(--border-radius-base) !important;
        }
        
        /* Animations */
        .fade-in {
            animation: fadeIn 0.4s var(--easing);
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(var(--space-4));
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* === RESPONSIVE DESIGN === */
        
        @media (max-width: 768px) {
            :root {
                --page-padding: var(--space-4);
                --section-padding: var(--space-6);
            }
            
            .control-bar {
                grid-template-columns: 1fr;
            }
            
            .dashboard-title {
                font-size: var(--font-size-3xl);
            }
            
            .card-body {
                padding: var(--space-4);
            }
        }
        
        @media (max-width: 480px) {
            .kpi-value {
                font-size: var(--font-size-2xl);
            }
            
            .control-card {
                padding: var(--space-4);
            }
        }
        
        /* === ACCESSIBILITY === */
        
        /* High contrast mode support */
        @media (prefers-contrast: high) {
            :root {
                --border-color: rgba(255, 255, 255, 0.5);
                --border-color-hover: rgba(255, 255, 255, 0.8);
            }
            
            .card {
                border-width: 2px;
            }
        }
        
        /* Custom Scrollbars */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--color-bg-primary);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--color-surface);
            border-radius: var(--border-radius-base);
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--color-surface-hover);
        }
        
        /* Screen Reader Only */
        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
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
        dcc.Interval(id="auto-refresh", interval=60*1000, n_intervals=0),  # 60s refresh
        # ---------- HEADER ----------
        dbc.Row(
            dbc.Col(
                html.Div(
                    [
                        html.H1([
                            html.Span(html.I(className="fas fa-microchip", style={
                                "marginRight":"14px",
                                "color":"#3b82f6",
                                "filter":"drop-shadow(0 0 6px #3b82f6)"
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

        # ---------- KPI SUMMARY CARDS ----------
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div("Avg Temp (°C)", className="kpi-label"),
                html.Div(id="kpi-avg-temp", className="kpi-value")
            ]), className="card kpi"), xs=6, md=3, className="mb-3"),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div("Avg Humidity (%)", className="kpi-label"),
                html.Div(id="kpi-avg-humidity", className="kpi-value")
            ]), className="card kpi"), xs=6, md=3, className="mb-3"),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div("Avg Battery (%)", className="kpi-label"),
                html.Div(id="kpi-avg-battery", className="kpi-value")
            ]), className="card kpi"), xs=6, md=3, className="mb-3"),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div("Errors (24h)", className="kpi-label"),
                html.Div(id="kpi-errors", className="kpi-value")
            ]), className="card kpi"), xs=6, md=3, className="mb-3"),
        ], className="mb-4"),

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
                                labelStyle={
                                    "display": "inline-flex",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                    "padding": "0 var(--space-4)",
                                    "height": "var(--hit-target-min)",
                                    "lineHeight": "1"
                                }
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
                            color="#3b82f6",  # Accessible primary color
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
                            color="#3b82f6",  # Accessible primary color
                            children=dcc.Graph(id="battery-overview", config={"displayModeBar": False})
                        )
                    ]), className="card"
                ), width=12, className="fade-in"
            )
        ], className="mb-4"),

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
    [Input("device-select", "value"), Input("metric-select", "value"), Input("status-filter", "value"), Input("auto-refresh", "n_intervals")]
)
def update_metric_timeseries(device_id, metric, statuses, _n):
    df = load_dataframe()
    device_df = df[df['device_id'] == device_id]
    device_df = device_df[device_df['status'].isin(statuses)]
    if device_df.empty:
        fig = go.Figure()
        fig.update_layout(title="No data for selection", template="plotly_dark")
        return fig
    meta = METRIC_META.get(metric, {"label": metric, "unit": "", "decimals": 2})
    fig = px.line(device_df, x='date', y=metric, title=f"Device {device_id}: {meta['label']} over Time")
    fig.update_traces(
        mode='lines+markers', 
        marker=dict(size=8, line=dict(width=2, color="#1f2937")),
        line=dict(width=3, color="#3b82f6"),  # Accessible blue
        connectgaps=True
    )
    # Hover formatting
    decimals = meta['decimals']
    unit = meta['unit']
    hover_tmpl = (
        f"<b>{{{{x|%b %d, %Y}}}}</b><br>{meta['label']}: {{{{y:.{decimals}f}}}}{unit}<extra></extra>"
    )
    fig.update_traces(hovertemplate=hover_tmpl)
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(17, 24, 39, 0.8)",  # Subtle background
        paper_bgcolor="rgba(0, 0, 0, 0)",
        font=dict(
            family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif",
            color="#d1d5db",  # Accessible text color
            size=13
        ),
        height=420,
        margin=dict(t=60, b=50, l=60, r=30),
        xaxis=dict(
            gridcolor="rgba(156, 163, 175, 0.1)",
            gridwidth=1,
            showgrid=True
        ),
        yaxis=dict(
            gridcolor="rgba(156, 163, 175, 0.1)", 
            gridwidth=1,
            showgrid=True
        )
    )
    yaxis_title = meta['label']
    if unit and unit not in yaxis_title:
        yaxis_title = f"{yaxis_title}"
    fig.update_yaxes(title=yaxis_title, ticksuffix=(unit if unit in ["%","°C"] else None))
    fig.update_xaxes(tickformat="%b %d", title="Date")
    return fig

@app.callback(
    Output("battery-overview", "figure"),
    [Input("status-filter", "value"), Input("auto-refresh", "n_intervals")]
)
def update_battery_overview(statuses, _n):
    df = load_dataframe()
    latest = df.sort_values(['device_id','date']).groupby('device_id').tail(1)
    all_devices_df = pd.DataFrame({'device_id': DEVICE_IDS})
    latest = all_devices_df.merge(latest, on='device_id', how='left')
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
        plot_bgcolor="rgba(17, 24, 39, 0.8)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
        font=dict(
            family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif",
            color="#d1d5db",
            size=13
        ),
        height=420,
        margin=dict(t=60, b=50, l=60, r=30),
        xaxis=dict(
            gridcolor="rgba(156, 163, 175, 0.1)",
            gridwidth=1,
            showgrid=False  
        ),
        yaxis=dict(
            gridcolor="rgba(156, 163, 175, 0.1)",
            gridwidth=1,
            showgrid=True
        )
    )
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside',
                      hovertemplate="%{x}<br>Battery: %{y:.1f}%<br>Status: %{customdata}<extra></extra>",
                      customdata=latest['status'])
    fig.update_yaxes(title="Battery (%)", ticksuffix="%")
    fig.update_xaxes(title="Device")
    return fig

@app.callback(
    Output("summary-text", "children"),
    [Input("status-filter", "value"), Input("auto-refresh", "n_intervals")]
)
def update_summary(statuses, _n):
    df = load_dataframe()
    latest = df.sort_values('date').groupby('device_id').tail(1)
    total = len(latest)
    counts = latest['status'].value_counts().to_dict()
    parts = [f"{k}:{counts.get(k,0)}" for k in STATUS_COLORS.keys() if k in statuses]
    last_date = df['date'].max().date().isoformat()
    return f"Devices: {total} • Status breakdown (filtered): {' | '.join(parts)} • Last update day in CSV: {last_date}"


@app.callback(
    Output("kpi-avg-temp", "children"),
    Output("kpi-avg-humidity", "children"),
    Output("kpi-avg-battery", "children"),
    Output("kpi-errors", "children"),
    Input("auto-refresh", "n_intervals")
)
def update_kpis(_n):
    df = load_dataframe()
    if df.empty:
        return "-", "-", "-", "-"
    latest = df.sort_values('date').groupby('device_id').tail(1)
    return (
        f"{latest['temperature_c'].mean():.1f}",
        f"{latest['humidity_pct'].mean():.1f}",
        f"{latest['battery_pct'].mean():.1f}",
        f"{int(latest['error_count'].sum())}"
    )


# --------------------------------------------------
# 5.  RUN SERVER
# --------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)