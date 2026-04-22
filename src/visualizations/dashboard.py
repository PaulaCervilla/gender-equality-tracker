"""Build an interactive HTML dashboard from processed data."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

import config

log = logging.getLogger(__name__)


# ---- Theme -----------------------------------------------------------------

BRAND_PRIMARY = "#4b2e83"      # deep purple
BRAND_ACCENT = "#c2185b"        # magenta
BRAND_TEAL = "#0e9594"
BRAND_GOLD = "#e0a458"
PALETTE = ["#4b2e83", "#c2185b", "#0e9594", "#e0a458",
           "#1f77b4", "#9467bd", "#2ca02c", "#d62728"]

_BASE_FONT = dict(family="Inter, -apple-system, 'Segoe UI', Roboto, sans-serif",
                  size=13, color="#2a2a3c")

# Register a custom Plotly template so every chart looks consistent.
pio.templates["equality"] = go.layout.Template(
    layout=go.Layout(
        font=_BASE_FONT,
        title=dict(font=dict(size=16, color="#1a1a2e", family=_BASE_FONT["family"]),
                   x=0.02, xanchor="left", y=0.96),
        colorway=PALETTE,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=50, r=20, t=60, b=50),
        xaxis=dict(showgrid=True, gridcolor="#eef0f4", zeroline=False,
                   linecolor="#cfd2da", ticks="outside", tickcolor="#cfd2da"),
        yaxis=dict(showgrid=True, gridcolor="#eef0f4", zeroline=False,
                   linecolor="#cfd2da", ticks="outside", tickcolor="#cfd2da"),
        legend=dict(bgcolor="rgba(255,255,255,0.85)", bordercolor="#e3e5ec",
                    borderwidth=1, font=dict(size=12)),
        hoverlabel=dict(bgcolor="white", font=dict(size=12, family=_BASE_FONT["family"]),
                        bordercolor="#cfd2da"),
    )
)
pio.templates.default = "equality"


# ---- Individual chart builders --------------------------------------------


def choropleth_score(snapshot: pd.DataFrame) -> go.Figure:
    df = snapshot.dropna(subset=["gender_equality_score"])
    fig = px.choropleth(
        df,
        locations="country_code",
        color="gender_equality_score",
        hover_name="country",
        color_continuous_scale="Viridis",
        range_color=(0, 100),
        labels={"gender_equality_score": "Score"},
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=500,
        coloraxis_colorbar=dict(thickness=14, len=0.7, tickfont=dict(size=11)),
        geo=dict(showframe=False, showcoastlines=False, projection_type="natural earth",
                 bgcolor="white"),
    )
    return fig


def labor_participation_trend(long_df: pd.DataFrame) -> go.Figure:
    """Female vs Male labor force participation — faceted side-by-side panels.

    Uses a hand-picked basket of large, regionally diverse countries so the
    chart stays readable. Each country gets a single colour shared between
    the two panels (Female | Male) — solid lines throughout.
    """
    sub = long_df[
        long_df["indicator_name"].isin(
            ["labor_force_participation_female", "labor_force_participation_male"]
        )
    ].copy()

    if sub.empty:
        return go.Figure().update_layout(title="Labor Force Participation (no data)")

    selected = ["USA", "GBR", "DEU", "ESP", "JPN", "BRA", "IND", "ZAF"]
    sub = sub[sub["country_code"].isin(selected)]

    label_map = {
        "labor_force_participation_female": "Female",
        "labor_force_participation_male": "Male",
    }
    sub["Gender"] = sub["indicator_name"].map(label_map)

    fig = px.line(
        sub.sort_values("year"),
        x="year",
        y="value",
        color="country",
        facet_col="Gender",
        category_orders={"Gender": ["Female", "Male"]},
        labels={"value": "% of population aged 15+", "year": ""},
    )
    fig.update_traces(line=dict(width=2.5))
    fig.update_layout(
        height=460,
        legend_title_text="",
        legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
        margin=dict(l=50, r=20, t=50, b=80),
    )
    fig.for_each_annotation(lambda a: a.update(
        text=f"<b>{a.text.split('=')[-1]}</b>",
        font=dict(size=14, color="#1a1a2e"),
    ))
    fig.update_yaxes(matches="y", rangemode="tozero")
    return fig


def wage_gap_bar(oecd_df: pd.DataFrame) -> go.Figure:
    if oecd_df.empty:
        return go.Figure().update_layout(title="Gender Wage Gap (no data)")
    latest = (
        oecd_df.sort_values("year")
        .groupby("country_code", as_index=False)
        .tail(1)
        .sort_values("gender_wage_gap_pct", ascending=True)
    )
    fig = px.bar(
        latest,
        x="gender_wage_gap_pct",
        y="country",
        orientation="h",
        color="gender_wage_gap_pct",
        color_continuous_scale=[(0, "#0e9594"), (0.5, "#e0a458"), (1, "#c2185b")],
        labels={"gender_wage_gap_pct": "Wage Gap (%)", "country": ""},
        text="gender_wage_gap_pct",
    )
    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside",
        cliponaxis=False,
        marker_line_width=0,
    )
    fig.update_layout(
        height=620,
        coloraxis_showscale=False,
        margin=dict(l=160, r=80, t=20, b=40),
        xaxis_title="Gender Wage Gap (%)",
    )
    fig.update_yaxes(automargin=True, tickfont=dict(size=12))
    return fig


def education_vs_labor_scatter(snapshot: pd.DataFrame) -> go.Figure:
    df = snapshot.dropna(
        subset=["literacy_female", "labor_force_participation_female",
                "women_in_parliament"]
    )
    df = df[df["women_in_parliament"] >= 0]
    if df.empty:
        return go.Figure().update_layout(title="Education vs Labor (no data)")

    fig = px.scatter(
        df,
        x="literacy_female",
        y="labor_force_participation_female",
        size="women_in_parliament",
        color="gender_equality_score",
        hover_name="country",
        color_continuous_scale="Viridis",
        size_max=40,
        opacity=0.85,
        labels={
            "literacy_female": "Female Literacy Rate (%)",
            "labor_force_participation_female": "Female Labor Force Participation (%)",
            "women_in_parliament": "Women in Parliament (%)",
            "gender_equality_score": "Equality Score",
        },
        trendline="ols" if _has_statsmodels() else None,
    )
    fig.update_traces(marker=dict(line=dict(width=0.5, color="white")))
    fig.update_layout(
        height=480,
        margin=dict(l=60, r=20, t=20, b=60),
        coloraxis_colorbar=dict(thickness=14, len=0.8),
    )
    return fig


def sentiment_timeline(news_df: pd.DataFrame) -> go.Figure:
    if news_df.empty or "sentiment_compound" not in news_df.columns:
        return go.Figure().update_layout(title="News Sentiment (no data)")

    df = news_df.dropna(subset=["published"]).copy()
    if df.empty:
        return go.Figure().update_layout(title="News Sentiment (no dated headlines)")

    df["date"] = pd.to_datetime(df["published"], utc=True).dt.date
    daily = (
        df.groupby("date")
        .agg(avg_sentiment=("sentiment_compound", "mean"),
             headlines=("title", "count"))
        .reset_index()
    )

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=daily["date"], y=daily["headlines"],
            name="Headlines",
            marker=dict(color="#e3e5ec"),
            hovertemplate="%{x|%b %d, %Y}<br>%{y} headlines<extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=daily["date"], y=daily["avg_sentiment"],
            name="Avg sentiment",
            mode="lines+markers",
            line=dict(color=BRAND_ACCENT, width=2.5, shape="spline"),
            marker=dict(size=7, color=BRAND_ACCENT,
                        line=dict(width=1, color="white")),
            hovertemplate="%{x|%b %d, %Y}<br>Sentiment: %{y:.3f}<extra></extra>",
        ),
        secondary_y=True,
    )
    fig.add_hline(y=0, line=dict(color="#cfd2da", width=1, dash="dot"),
                  secondary_y=True)
    fig.update_layout(
        height=420,
        margin=dict(l=50, r=50, t=20, b=50),
        legend=dict(orientation="h", y=1.1, x=1, xanchor="right"),
        bargap=0.2,
    )
    fig.update_yaxes(title_text="Headline count", secondary_y=False, showgrid=False)
    fig.update_yaxes(title_text="Sentiment (compound)", secondary_y=True,
                     range=[-1, 1])
    return fig


def sentiment_donut(news_df: pd.DataFrame) -> go.Figure:
    """Compact donut summarising the distribution of headline sentiment."""
    if news_df.empty or "sentiment_label" not in news_df.columns:
        return go.Figure().update_layout(title="Sentiment (no data)")

    counts = news_df["sentiment_label"].value_counts().reindex(
        ["positive", "neutral", "negative"], fill_value=0
    )
    colors = {"positive": "#0e9594", "neutral": "#cfd2da", "negative": "#c2185b"}

    fig = go.Figure(go.Pie(
        labels=[s.capitalize() for s in counts.index],
        values=counts.values,
        hole=0.6,
        marker=dict(colors=[colors[s] for s in counts.index],
                    line=dict(color="white", width=2)),
        textinfo="label+percent",
        textfont=dict(size=12),
        sort=False,
    ))
    fig.update_layout(
        height=360,
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=False,
        annotations=[dict(text=f"<b>{int(counts.sum())}</b><br>headlines",
                          x=0.5, y=0.5, showarrow=False,
                          font=dict(size=14, color="#1a1a2e"))],
    )
    return fig


# ---- KPI helpers -----------------------------------------------------------


def _kpis(snapshot: pd.DataFrame, news_df: pd.DataFrame, oecd_df: pd.DataFrame) -> list[dict]:
    scored = snapshot.dropna(subset=["gender_equality_score"])
    top_row = scored.sort_values("gender_equality_score", ascending=False).head(1)
    top_country = top_row["country"].iloc[0] if not top_row.empty else "—"
    top_score = top_row["gender_equality_score"].iloc[0] if not top_row.empty else 0
    mean_score = scored["gender_equality_score"].mean() if not scored.empty else 0

    if not oecd_df.empty:
        latest_oecd = (oecd_df.sort_values("year")
                       .groupby("country_code", as_index=False).tail(1))
        avg_gap = latest_oecd["gender_wage_gap_pct"].mean()
    else:
        avg_gap = 0

    return [
        {"label": "Countries scored", "value": f"{len(scored)}",
         "sub": "across 12 indicators"},
        {"label": "Avg equality score", "value": f"{mean_score:.1f}",
         "sub": "out of 100"},
        {"label": "Top country", "value": top_country,
         "sub": f"score {top_score:.1f}"},
        {"label": "Avg OECD wage gap", "value": f"{avg_gap:.1f}%",
         "sub": f"{len(news_df)} headlines analysed"},
    ]


# ---- HTML scaffolding ------------------------------------------------------

_HTML_TEMPLATE = """\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Gender Equality Tracker</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {{
    --brand: #4b2e83;
    --accent: #c2185b;
    --teal: #0e9594;
    --bg: #f4f5fa;
    --surface: #ffffff;
    --text: #1a1a2e;
    --muted: #6b6f7e;
    --border: #e6e8ef;
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; }}
  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
  }}

  /* ===== Hero ===== */
  .hero {{
    background: linear-gradient(135deg, #4b2e83 0%, #c2185b 100%);
    color: white;
    padding: 3.5rem 1.5rem 5rem;
    position: relative;
    overflow: hidden;
  }}
  .hero::after {{
    content: "";
    position: absolute; inset: 0;
    background: radial-gradient(circle at 80% 20%, rgba(255,255,255,0.12), transparent 50%);
    pointer-events: none;
  }}
  .hero-inner {{ max-width: 1200px; margin: 0 auto; position: relative; }}
  .hero .eyebrow {{
    text-transform: uppercase; letter-spacing: .15em; font-size: .75rem;
    opacity: .85; margin-bottom: .75rem; font-weight: 600;
  }}
  .hero h1 {{
    margin: 0; font-size: clamp(1.8rem, 4vw, 2.75rem);
    font-weight: 800; letter-spacing: -.02em;
  }}
  .hero p {{ margin-top: .75rem; max-width: 720px; opacity: .92; font-size: 1.05rem; }}

  /* ===== KPI strip ===== */
  .kpis {{
    max-width: 1200px; margin: -3rem auto 0; padding: 0 1.5rem;
    display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem; position: relative;
  }}
  .kpi {{
    background: var(--surface); border-radius: 14px; padding: 1.25rem 1.5rem;
    box-shadow: 0 8px 24px rgba(20, 20, 50, 0.08);
    border: 1px solid var(--border);
  }}
  .kpi .label {{
    text-transform: uppercase; font-size: .7rem; font-weight: 600;
    color: var(--muted); letter-spacing: .08em;
  }}
  .kpi .value {{
    font-size: 1.85rem; font-weight: 700; color: var(--text);
    margin-top: .35rem; line-height: 1.1;
  }}
  .kpi .sub {{ color: var(--muted); font-size: .8rem; margin-top: .25rem; }}

  /* ===== Layout ===== */
  main {{ max-width: 1200px; margin: 2rem auto; padding: 0 1.5rem 3rem; }}
  .grid {{ display: grid; grid-template-columns: 1fr; gap: 1.5rem; }}
  .row-2 {{ display: grid; grid-template-columns: 1fr; gap: 1.5rem; }}
  @media (min-width: 900px) {{
    .row-2 {{ grid-template-columns: 1.6fr 1fr; }}
  }}

  .card {{
    background: var(--surface); border-radius: 14px; padding: 1.5rem;
    box-shadow: 0 4px 16px rgba(20, 20, 50, 0.05);
    border: 1px solid var(--border);
  }}
  .card h2 {{
    margin: 0 0 .25rem; font-size: 1.15rem; font-weight: 700; letter-spacing: -.01em;
  }}
  .card .desc {{
    margin: 0 0 1rem; color: var(--muted); font-size: .9rem;
  }}
  .card .source {{
    margin-top: .75rem; color: var(--muted); font-size: .75rem;
    font-style: italic;
  }}

  /* ===== Footer ===== */
  footer {{
    background: var(--text); color: #cfd2da;
    text-align: center; padding: 2rem 1rem; font-size: .85rem;
  }}
  footer a {{ color: #fff; text-decoration: none; border-bottom: 1px dotted #cfd2da; }}
  footer .stack {{ margin-top: .5rem; opacity: .65; font-size: .75rem; }}
</style>
</head>
<body>

<header class="hero">
  <div class="hero-inner">
    <div class="eyebrow">Data Pipeline · Visualisation · NLP</div>
    <h1>Gender Equality Tracker</h1>
    <p>An end-to-end Python project that pulls public data from the World Bank
    and OECD, scrapes live news, and turns it into a single composite score
    measuring gender equality across {country_count} countries.</p>
  </div>
</header>

<section class="kpis">
{kpi_html}
</section>

<main>
  <div class="grid">

    <div class="card">
      <h2>🌍 Composite Gender Equality Score</h2>
      <p class="desc">Weighted average of 6 sub-indicators (labor participation,
      women in parliament, literacy, wage workers, unemployment gap, school
      enrolment parity). Higher = more equal.</p>
      {fig_choropleth}
      <p class="source">Source: World Bank Indicators API · methodology in <code>config.py</code></p>
    </div>

    <div class="row-2">
      <div class="card">
        <h2>💼 Gender Wage Gap by Country</h2>
        <p class="desc">Difference between male and female median earnings, latest
        OECD figure for each country.</p>
        {fig_wage_gap}
        <p class="source">Source: OECD SDMX — Gender Wage Gap dataset</p>
      </div>
      <div class="card">
        <h2>📰 News Sentiment Mix</h2>
        <p class="desc">VADER-classified tone of all gender-equality headlines
        collected this run.</p>
        {fig_donut}
        <p class="source">Source: Google News RSS · VADER sentiment</p>
      </div>
    </div>

    <div class="card">
      <h2>📈 Labor Force Participation Over Time</h2>
      <p class="desc">Female (left) vs male (right) labor participation for a
      diverse basket of 8 economies. Each colour is one country across both
      panels.</p>
      {fig_trend}
      <p class="source">Source: World Bank · indicators SL.TLF.CACT.FE.ZS / SL.TLF.CACT.MA.ZS</p>
    </div>

    <div class="card">
      <h2>🎓 Education Drives Workforce Participation</h2>
      <p class="desc">Each bubble is a country. Larger bubbles = more women in
      parliament. Colour reflects the composite Equality Score.</p>
      {fig_scatter}
      <p class="source">Source: World Bank — latest available value per country</p>
    </div>

    <div class="card">
      <h2>🗞️ Headline Volume & Sentiment</h2>
      <p class="desc">Daily news activity (bars) and average sentiment (line) for
      gender-equality headlines pulled from Google News.</p>
      {fig_sentiment}
      <p class="source">Source: Google News RSS · VADER compound score</p>
    </div>

  </div>
</main>

<footer>
  <div>
    Built with <strong>Python</strong> · pandas · Plotly · BeautifulSoup · VADER ·
    <a href="https://github.com/PaulaCervilla/gender-equality-tracker" target="_blank" rel="noopener">view source on GitHub</a>
  </div>
  <div class="stack">© 2026 Gender Equality Tracker · data pulled {today}</div>
</footer>

</body>
</html>
"""


def _kpi_html(kpis: list[dict]) -> str:
    rows = []
    for k in kpis:
        rows.append(
            f'<div class="kpi">'
            f'<div class="label">{k["label"]}</div>'
            f'<div class="value">{k["value"]}</div>'
            f'<div class="sub">{k["sub"]}</div>'
            f'</div>'
        )
    return "\n".join(rows)


def _fig_html(fig: go.Figure, include_js: bool) -> str:
    return fig.to_html(
        full_html=False,
        include_plotlyjs="cdn" if include_js else False,
        config={"displaylogo": False, "responsive": True,
                "modeBarButtonsToRemove": ["lasso2d", "select2d"]},
    )


def build_dashboard(
    snapshot: pd.DataFrame,
    long_df: pd.DataFrame,
    oecd_df: pd.DataFrame,
    news_df: pd.DataFrame,
    output_path: Path | None = None,
) -> Path:
    output_path = output_path or (config.OUTPUT_DIR / "dashboard.html")

    fig_choropleth = choropleth_score(snapshot)
    fig_wage_gap = wage_gap_bar(oecd_df)
    fig_donut = sentiment_donut(news_df)
    fig_trend = labor_participation_trend(long_df)
    fig_scatter = education_vs_labor_scatter(snapshot)
    fig_sentiment = sentiment_timeline(news_df)

    kpis = _kpis(snapshot, news_df, oecd_df)
    country_count = snapshot["gender_equality_score"].notna().sum()

    html = _HTML_TEMPLATE.format(
        kpi_html=_kpi_html(kpis),
        country_count=int(country_count),
        today=pd.Timestamp.now().strftime("%b %Y"),
        fig_choropleth=_fig_html(fig_choropleth, include_js=True),
        fig_wage_gap=_fig_html(fig_wage_gap, include_js=False),
        fig_donut=_fig_html(fig_donut, include_js=False),
        fig_trend=_fig_html(fig_trend, include_js=False),
        fig_scatter=_fig_html(fig_scatter, include_js=False),
        fig_sentiment=_fig_html(fig_sentiment, include_js=False),
    )

    output_path.write_text(html, encoding="utf-8")
    log.info("Dashboard written to %s", output_path)
    return output_path


def _has_statsmodels() -> bool:
    try:
        import statsmodels  # noqa: F401
    except ImportError:
        return False
    return True
