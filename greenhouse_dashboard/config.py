from pathlib import Path


APP_TITLE = "Greenhouse Decision Support"
DATA_FILE = Path(__file__).resolve().parent.parent / "greenhouse_systems_cleaned.csv"

TRUE_VALUES = {"true", "yes", "y", "1"}
SYSTEM_DISPLAY_NAMES = {
    "Conventional": "Conventional",
    "Tower": "Towers",
    "A-shape + Gutters": "A-shape + Gutters",
}
SYSTEM_ORDER = ["Conventional", "Towers", "A-shape + Gutters"]
SYSTEM_COLORS = {
    "Conventional": "#475569",
    "Towers": "#0f766e",
    "A-shape + Gutters": "#c2410c",
}

PAGE_META = {
    "Dashboard": {
        "icon": "📊",
        "nav_label": "📊 Dashboard",
        "context": "Visibility",
        "title": "Executive Decision Dashboard",
        "subtitle": (
            "A leadership view of greenhouse performance, resource consumption, and system trade-offs "
            "across Conventional, Towers, and A-shape + Gutters."
        ),
    },
    "System Comparison": {
        "icon": "⚖️",
        "nav_label": "⚖️ System Comparison",
        "context": "Comparison",
        "title": "System Comparison Center",
        "subtitle": (
            "A side-by-side comparison of performance, efficiency, risk, and confidence so decision makers "
            "can see where each system wins and where caution is required."
        ),
    },
    "Cost Optimization": {
        "icon": "💲",
        "nav_label": "💲 Cost Optimization",
        "context": "Efficiency",
        "title": "Cost And Efficiency Review",
        "subtitle": (
            "Estimated operating cost, resource intensity, and savings opportunities designed to show "
            "where management attention can reduce spend."
        ),
    },
    "Problem Detection": {
        "icon": "⚠️",
        "nav_label": "⚠️ Problem Detection",
        "context": "Risk Prevention",
        "title": "Risk And Early Problem Detection",
        "subtitle": (
            "Rule-based monitoring for operational incidents, leak incidents, instability, and abnormal "
            "water behavior before they become larger losses."
        ),
    },
    "Scenario Simulation": {
        "icon": "🧪",
        "nav_label": "🧪 Scenario Simulation",
        "context": "Planning",
        "title": "Scenario Simulation",
        "subtitle": (
            "Test how cost assumptions and future yield placeholders could change rankings, total spend, "
            "and the recommended operating system."
        ),
    },
    "Methodology": {
        "icon": "📘",
        "nav_label": "📘 Methodology",
        "context": "Research",
        "title": "Methodology And Research Notes",
        "subtitle": (
            "Project objective, scoring logic, assumptions, limitations, and why the current results should "
            "be interpreted as operational proxies rather than full production economics."
        ),
    },
}

DECISION_MODE_OPTIONS = [
    "Balanced",
    "Cost Minimization",
    "Risk Reduction",
    "Sustainability",
    "Yield Maximization",
]

DECISION_MODE_COPY = {
    "Balanced": "Balanced view across efficiency, risk, and operating discipline.",
    "Cost Minimization": "Favors lower cost intensity and resource spend.",
    "Risk Reduction": "Favors incident control, leak prevention, and stability.",
    "Sustainability": "Favors lower water and nutrient intensity with risk guardrails.",
    "Yield Maximization": "Future-ready placeholder for yield-led decisions once harvest data exists.",
}

COMPARISON_BASIS_OPTIONS = [
    "Full dataset view",
    "Overlapping comparison window",
]

COLORS = {
    "ink": "#17211d",
    "muted": "#66746f",
    "border": "#dfe7e3",
    "panel": "#ffffff",
    "canvas": "#f6f8f7",
    "water": "#0f766e",
    "water_fill": "#dff4ef",
    "nutrient": "#b7791f",
    "nutrient_fill": "#fcf1df",
    "incident": "#2563eb",
    "incident_fill": "#dce8ff",
    "leak": "#dc2626",
    "leak_fill": "#fee2e2",
    "score": "#3157d5",
    "cost": "#0f766e",
    "success": "#15803d",
    "warning": "#d97706",
}

DEFAULT_COST_MODEL = {
    "water_cost_per_l": 0.0015,
    "nutrient_cost_per_ml": 0.0100,
    "energy_cost_per_active_day": 0.0,
}

OUTCOME_SCORE_WEIGHTS = {
    "yield_performance": 0.26,
    "cost_per_kg": 0.18,
    "water_per_kg": 0.14,
    "nutrient_per_kg": 0.10,
    "incident_day_rate_pct": 0.14,
    "leak_day_rate_pct": 0.10,
    "daily_water_volatility_pct": 0.08,
}

PROXY_SCORE_WEIGHTS = {
    "estimated_cost_per_100_plants": 0.24,
    "water_per_100_plants_l": 0.18,
    "nutrient_per_100_plants_ml": 0.10,
    "incident_day_rate_pct": 0.20,
    "leak_day_rate_pct": 0.16,
    "daily_water_volatility_pct": 0.12,
}

EFFICIENCY_SCORE_WEIGHTS = {
    "estimated_cost_per_100_plants": 0.40,
    "water_per_100_plants_l": 0.35,
    "nutrient_per_100_plants_ml": 0.25,
}

RISK_SCORE_WEIGHTS = {
    "incident_day_rate_pct": 0.45,
    "leak_day_rate_pct": 0.35,
    "daily_water_volatility_pct": 0.20,
}

PROXY_MODE_WEIGHTS = {
    "Balanced": PROXY_SCORE_WEIGHTS,
    "Cost Minimization": {
        "estimated_cost_per_100_plants": 0.38,
        "water_per_100_plants_l": 0.22,
        "nutrient_per_100_plants_ml": 0.12,
        "incident_day_rate_pct": 0.14,
        "leak_day_rate_pct": 0.08,
        "daily_water_volatility_pct": 0.06,
    },
    "Risk Reduction": {
        "estimated_cost_per_100_plants": 0.10,
        "water_per_100_plants_l": 0.10,
        "nutrient_per_100_plants_ml": 0.05,
        "incident_day_rate_pct": 0.31,
        "leak_day_rate_pct": 0.27,
        "daily_water_volatility_pct": 0.17,
    },
    "Sustainability": {
        "estimated_cost_per_100_plants": 0.16,
        "water_per_100_plants_l": 0.36,
        "nutrient_per_100_plants_ml": 0.24,
        "incident_day_rate_pct": 0.12,
        "leak_day_rate_pct": 0.07,
        "daily_water_volatility_pct": 0.05,
    },
    "Yield Maximization": PROXY_SCORE_WEIGHTS,
}

OUTCOME_MODE_WEIGHTS = {
    "Balanced": OUTCOME_SCORE_WEIGHTS,
    "Cost Minimization": {
        "yield_performance": 0.16,
        "cost_per_kg": 0.28,
        "water_per_kg": 0.16,
        "nutrient_per_kg": 0.10,
        "incident_day_rate_pct": 0.12,
        "leak_day_rate_pct": 0.10,
        "daily_water_volatility_pct": 0.08,
    },
    "Risk Reduction": {
        "yield_performance": 0.12,
        "cost_per_kg": 0.10,
        "water_per_kg": 0.08,
        "nutrient_per_kg": 0.05,
        "incident_day_rate_pct": 0.28,
        "leak_day_rate_pct": 0.22,
        "daily_water_volatility_pct": 0.15,
    },
    "Sustainability": {
        "yield_performance": 0.14,
        "cost_per_kg": 0.14,
        "water_per_kg": 0.27,
        "nutrient_per_kg": 0.20,
        "incident_day_rate_pct": 0.12,
        "leak_day_rate_pct": 0.07,
        "daily_water_volatility_pct": 0.06,
    },
    "Yield Maximization": {
        "yield_performance": 0.40,
        "cost_per_kg": 0.16,
        "water_per_kg": 0.12,
        "nutrient_per_kg": 0.08,
        "incident_day_rate_pct": 0.12,
        "leak_day_rate_pct": 0.07,
        "daily_water_volatility_pct": 0.05,
    },
}

YIELD_CANDIDATES = [
    "yield_kg",
    "yield",
    "harvest_kg",
    "harvest_weight_kg",
    "harvest_quantity_kg",
    "harvest_quantity",
]
AREA_CANDIDATES = ["area_m2", "area_sq_m", "growing_area_m2"]
QUALITY_CANDIDATES = ["quality_score", "quality_index"]


def build_styles() -> str:
    return f"""
    <style>
        :root {{
            --ink: {COLORS["ink"]};
            --muted: {COLORS["muted"]};
            --border: {COLORS["border"]};
            --panel: {COLORS["panel"]};
            --canvas: {COLORS["canvas"]};
            --water: {COLORS["water"]};
            --incident: {COLORS["incident"]};
            --leak: {COLORS["leak"]};
            --radius-lg: 20px;
            --radius-md: 16px;
            --radius-sm: 12px;
            --shadow-soft: 0 1px 2px rgba(16, 24, 40, 0.03), 0 10px 28px rgba(16, 24, 40, 0.04);
            --line: #e8eeeb;
        }}

        html, body, [class*="css"] {{
            font-family: "Avenir Next", "Segoe UI", "Helvetica Neue", sans-serif;
        }}

        [data-testid="stAppViewContainer"] {{
            background: var(--canvas);
        }}

        [data-testid="stSidebar"] {{
            background: #fbfcfb;
            border-right: 1px solid var(--border);
        }}

        [data-testid="stSidebar"] .block-container {{
            padding-top: 1rem;
            padding-bottom: 1.25rem;
        }}

        .block-container {{
            max-width: 1380px;
            padding-top: 1.15rem;
            padding-bottom: 2.2rem;
        }}

        [data-testid="stSidebar"] div[role="radiogroup"] > label {{
            background: transparent;
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 0.72rem 0.82rem;
            margin-bottom: 0.55rem;
            transition: all 0.18s ease;
        }}

        [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {{
            background: #ffffff;
            border-color: #ccd9ff;
            box-shadow: inset 0 0 0 1px #ccd9ff;
        }}

        [data-testid="stSidebar"] div[role="radiogroup"] > label:hover {{
            border-color: #cad6d1;
            background: #ffffff;
        }}

        [data-testid="stSidebar"] div[role="radiogroup"] > label p {{
            color: var(--ink);
            font-size: 0.95rem;
            font-weight: 700;
        }}

        [data-testid="metric-container"] {{
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 1rem 1.05rem;
            box-shadow: none;
            min-height: 112px;
        }}

        [data-testid="metric-container"] [data-testid="stMetricValue"] {{
            color: var(--ink);
            font-size: 1.55rem;
            font-weight: 800;
            line-height: 1.08;
        }}

        [data-testid="metric-container"] label {{
            color: var(--muted);
            font-weight: 700;
            letter-spacing: 0.01em;
        }}

        [data-testid="metric-container"] [data-testid="stMetricDelta"] {{
            font-size: 0.8rem;
            font-weight: 700;
        }}

        div[data-baseweb="select"] > div,
        div[data-testid="stDateInputField"] {{
            background: #ffffff;
            border-color: var(--border);
            border-radius: 14px;
            min-height: 46px;
            box-shadow: none;
        }}

        div[data-baseweb="select"] > div:hover,
        div[data-testid="stDateInputField"]:hover {{
            border-color: #c8d4cf;
        }}

        .stMultiSelect label,
        .stDateInput label,
        .stNumberInput label {{
            color: var(--muted);
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.01em;
            margin-bottom: 0.32rem;
        }}

        [data-testid="stHorizontalBlock"] > div:has(.summary-card),
        [data-testid="stHorizontalBlock"] > div:has(.decision-card) {{
            height: 100%;
        }}

        .nav-card,
        .hero-shell,
        .summary-card,
        .decision-card,
        .recommendation-shell,
        .methodology-shell {{
            background: var(--panel);
            border: 1px solid var(--border);
            box-shadow: var(--shadow-soft);
        }}

        .nav-card {{
            border-radius: var(--radius-lg);
            padding: 0.95rem 1rem;
            margin-bottom: 0.9rem;
        }}

        .nav-kicker {{
            color: {COLORS["score"]};
            font-size: 0.72rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-weight: 800;
            margin-bottom: 0.22rem;
        }}

        .nav-title {{
            color: var(--ink);
            font-size: 1.02rem;
            font-weight: 800;
            margin-bottom: 0.28rem;
        }}

        .nav-copy,
        .nav-footer,
        .muted-copy {{
            color: var(--muted);
            line-height: 1.5;
            font-size: 0.88rem;
        }}

        .nav-footer {{
            margin-top: 0.75rem;
            padding-top: 0.7rem;
            border-top: 1px solid var(--line);
        }}

        .toolbar-shell {{
            margin-bottom: 0.75rem;
        }}

        .toolbar-top {{
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 0.55rem;
        }}

        .hero-eyebrow,
        .section-eyebrow,
        .toolbar-eyebrow {{
            font-size: 0.72rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-weight: 800;
        }}

        .toolbar-eyebrow {{
            color: {COLORS["score"]};
            margin-bottom: 0.22rem;
        }}

        .toolbar-title {{
            color: var(--ink);
            font-size: 1rem;
            font-weight: 800;
            margin-bottom: 0;
        }}

        .toolbar-copy {{
            color: var(--muted);
            font-size: 0.86rem;
            line-height: 1.5;
            max-width: 460px;
        }}

        .toolbar-meta {{
            color: var(--muted);
            font-size: 0.84rem;
            line-height: 1.45;
            margin: 0.55rem 0 0.35rem;
        }}

        .hero-shell {{
            border-radius: 24px;
            padding: 1.35rem 1.45rem 1.2rem;
            margin-bottom: 1.15rem;
        }}

        .hero-top {{
            display: grid;
            grid-template-columns: minmax(0, 1.4fr) minmax(240px, 0.7fr);
            gap: 1rem;
            align-items: start;
            margin-bottom: 1rem;
        }}

        .hero-eyebrow {{
            color: {COLORS["score"]};
            margin-bottom: 0.28rem;
        }}

        .hero-title {{
            color: var(--ink);
            font-size: 2.1rem;
            line-height: 1.05;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin: 0 0 0.42rem;
        }}

        .hero-subtitle {{
            color: var(--muted);
            font-size: 0.96rem;
            line-height: 1.62;
            max-width: 760px;
            margin-bottom: 0;
        }}

        .hero-meta-card {{
            background: #fbfcfc;
            border: 1px solid var(--line);
            border-radius: var(--radius-md);
            padding: 0.95rem 1rem;
        }}

        .hero-meta-label {{
            color: var(--muted);
            font-size: 0.72rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-weight: 800;
            margin-bottom: 0.3rem;
        }}

        .hero-meta-value {{
            color: var(--ink);
            font-size: 1rem;
            font-weight: 800;
            margin-bottom: 0.18rem;
        }}

        .hero-meta-copy {{
            color: var(--muted);
            font-size: 0.88rem;
            line-height: 1.5;
        }}

        .hero-stat-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.75rem;
            padding-top: 1rem;
            border-top: 1px solid var(--line);
        }}

        .hero-stat {{
            background: #fbfcfc;
            border: 1px solid var(--line);
            border-radius: var(--radius-md);
            padding: 0.85rem 0.95rem;
        }}

        .hero-stat-label {{
            color: var(--muted);
            font-size: 0.74rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 700;
            margin-bottom: 0.26rem;
        }}

        .hero-stat-value {{
            color: var(--ink);
            font-size: 1.12rem;
            font-weight: 800;
        }}

        .section-shell {{
            margin-top: 1.8rem;
            margin-bottom: 0.85rem;
        }}

        .section-title {{
            color: var(--ink);
            font-size: 1.08rem;
            font-weight: 800;
            line-height: 1.3;
            margin-bottom: 0.16rem;
        }}

        .section-caption {{
            color: var(--muted);
            font-size: 0.9rem;
            line-height: 1.55;
            max-width: 760px;
            margin-bottom: 0;
        }}

        .metric-panel {{
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 1rem 1.05rem;
            box-shadow: none;
            min-height: 112px;
        }}

        .metric-panel-label {{
            color: var(--muted);
            font-size: 0.74rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.38rem;
        }}

        .metric-panel-value {{
            color: var(--ink);
            font-size: 1.52rem;
            line-height: 1.05;
            font-weight: 800;
            margin-bottom: 0.24rem;
        }}

        .metric-panel-detail {{
            color: var(--muted);
            font-size: 0.84rem;
            line-height: 1.48;
        }}

        .note-shell {{
            border-radius: var(--radius-lg);
            padding: 0.95rem 1.05rem;
            margin-bottom: 0.9rem;
            border: 1px solid var(--border);
            background: #ffffff;
        }}

        .note-soft {{
            background: #fbfcfc;
        }}

        .note-accent {{
            background: #f8faff;
            border-color: #dbe5ff;
        }}

        .note-warning {{
            background: #fffaf5;
            border-color: #f2dfc7;
        }}

        .note-title {{
            color: var(--ink);
            font-size: 0.92rem;
            font-weight: 800;
            margin-bottom: 0.38rem;
        }}

        .note-line {{
            color: var(--muted);
            font-size: 0.89rem;
            line-height: 1.55;
            margin-bottom: 0.24rem;
        }}

        .note-line:last-child {{
            margin-bottom: 0;
        }}

        .summary-card,
        .decision-card {{
            border-radius: var(--radius-lg);
            padding: 1rem 1.05rem;
            height: 100%;
        }}

        .exec-brief-shell {{
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 1.1rem 1.15rem;
            box-shadow: var(--shadow-soft);
            height: 100%;
        }}

        .exec-brief-kicker {{
            color: {COLORS["score"]};
            font-size: 0.72rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-weight: 800;
            margin-bottom: 0.28rem;
        }}

        .exec-brief-title {{
            color: var(--ink);
            font-size: 1.18rem;
            line-height: 1.28;
            font-weight: 800;
            margin-bottom: 0.45rem;
        }}

        .exec-brief-copy {{
            color: var(--muted);
            font-size: 0.92rem;
            line-height: 1.58;
            margin-bottom: 0.8rem;
        }}

        .exec-line {{
            display: grid;
            grid-template-columns: 118px 1fr;
            gap: 0.9rem;
            align-items: start;
            padding: 0.76rem 0;
        }}

        .exec-line + .exec-line {{
            border-top: 1px solid var(--line);
        }}

        .exec-line-label {{
            color: var(--muted);
            font-size: 0.72rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            font-weight: 800;
            padding-top: 0.16rem;
        }}

        .exec-line-body {{
            color: var(--ink);
            font-size: 0.92rem;
            line-height: 1.58;
        }}

        .mini-summary-card {{
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 1rem 1.05rem;
            box-shadow: var(--shadow-soft);
            margin-bottom: 0.75rem;
        }}

        .mini-summary-card:last-child {{
            margin-bottom: 0;
        }}

        .mini-summary-kicker {{
            color: {COLORS["score"]};
            font-size: 0.72rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-weight: 800;
            margin-bottom: 0.28rem;
        }}

        .mini-summary-title {{
            color: var(--ink);
            font-size: 0.98rem;
            font-weight: 800;
            line-height: 1.35;
            margin-bottom: 0.3rem;
        }}

        .mini-summary-value {{
            color: var(--ink);
            font-size: 1.18rem;
            font-weight: 800;
            margin-bottom: 0.28rem;
        }}

        .mini-summary-copy {{
            color: var(--muted);
            font-size: 0.88rem;
            line-height: 1.56;
        }}

        .summary-kicker {{
            color: {COLORS["score"]};
            font-size: 0.72rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-weight: 800;
            margin-bottom: 0.28rem;
        }}

        .summary-title {{
            color: var(--ink);
            font-size: 1rem;
            font-weight: 800;
            margin-bottom: 0.35rem;
            line-height: 1.35;
        }}

        .summary-value {{
            color: var(--ink);
            font-size: 1.28rem;
            font-weight: 800;
            margin-bottom: 0.3rem;
        }}

        .summary-copy,
        .decision-copy {{
            color: var(--muted);
            font-size: 0.88rem;
            line-height: 1.55;
        }}

        .decision-label {{
            color: var(--muted);
            font-size: 0.74rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 800;
            margin-bottom: 0.24rem;
        }}

        .decision-system {{
            color: var(--ink);
            font-size: 1.16rem;
            font-weight: 800;
            line-height: 1.28;
            margin-bottom: 0.22rem;
        }}

        .decision-metric {{
            color: {COLORS["score"]};
            font-size: 0.9rem;
            font-weight: 700;
            margin-bottom: 0.34rem;
        }}

        .recommendation-shell,
        .methodology-shell {{
            border-radius: var(--radius-lg);
            padding: 1rem 1.05rem;
        }}

        .recommendation-shell {{
            margin-bottom: 0.8rem;
        }}

        .recommendation-title,
        .methodology-title {{
            color: var(--ink);
            font-size: 1rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
        }}

        .recommendation-line,
        .methodology-line {{
            color: var(--muted);
            font-size: 0.9rem;
            line-height: 1.58;
            margin-bottom: 0.4rem;
        }}

        [data-testid="stExpander"] {{
            border-radius: var(--radius-lg);
            overflow: hidden;
            border: 1px solid var(--border);
            box-shadow: none;
            background: #ffffff;
            margin-bottom: 0.8rem;
        }}

        [data-testid="stExpander"] details summary p {{
            color: var(--ink);
            font-weight: 700;
            font-size: 0.92rem;
        }}

        div[data-testid="stVegaLiteChart"],
        div[data-testid="stAltairChart"] {{
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-soft);
            padding: 0.7rem 0.8rem 0.2rem;
        }}

        div[data-testid="stDataFrame"] {{
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-soft);
            padding: 0.22rem;
        }}

        .stButton button,
        .stDownloadButton button {{
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 14px;
            color: var(--ink);
            font-weight: 700;
            box-shadow: none;
        }}

        .stButton button:hover,
        .stDownloadButton button:hover {{
            border-color: #c8d4cf;
            color: var(--ink);
        }}

        [data-testid="stAlert"] {{
            border-radius: var(--radius-md);
            border: 1px solid var(--border);
        }}

        @media (max-width: 1040px) {{
            .toolbar-top,
            .hero-top {{
                grid-template-columns: 1fr;
                display: grid;
            }}

            .hero-stat-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
        }}

        @media (max-width: 640px) {{
            .hero-stat-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
    """
