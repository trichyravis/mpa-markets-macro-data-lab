"""Markets & Macro Data Lab — The Mountain Path Academy.
Free, official data for analysis and forecasting practice:
US Treasury yield curve history (US Treasury), India G-Sec curve (CCIL indicative yields),
credit spreads and India rate history (FRED public CSV), bond index performance (Yahoo Finance),
GDP and macro indicators (World Bank, IMF World Economic Outlook).
"""
import datetime as dt
import io
import re

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

GOLD, BLUE, MID, CARD = "#FFD700", "#003366", "#004d80", "#112240"
TXT, MUTED, GRN, RED, LB = "#e6f1ff", "#8892b0", "#28a745", "#dc3545", "#ADD8E6"
BG = "linear-gradient(135deg,#1a2332,#243447,#2a3f5f)"
SITE = "https://themountainpathacademy.com"
UA = {"User-Agent": "Mozilla/5.0 (education; themountainpathacademy.com)"}
PALETTE = [GOLD, LB, GRN, "#ff9f43", "#c084fc", RED, "#4dd0e1", "#f472b6", "#a3e635", "#fbbf24"]

st.set_page_config(page_title="Markets & Macro Data Lab | Mountain Path", page_icon="📈", layout="wide")
st.html(f"""<style>
.stApp{{background:{BG};}}
header[data-testid="stHeader"]{{background:transparent;}}
section[data-testid="stSidebar"]{{background:{CARD};border-right:1px solid {MID};}}
div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="select"] > div, div[data-baseweb="textarea"]{{
  background:#0b1a33!important;border:1px solid {MID}!important;}}
div[data-baseweb="input"] *, div[data-baseweb="base-input"], div[data-baseweb="select"] > div *,
div[data-testid="stTextInputRootElement"], div[data-testid="stNumberInputContainer"]{{background:#0b1a33!important;}}
input, textarea{{background:#0b1a33!important;color:{TXT}!important;-webkit-text-fill-color:{TXT}!important;caret-color:{GOLD};}}
input::placeholder{{color:{MUTED}!important;-webkit-text-fill-color:{MUTED}!important;opacity:1}}
div[data-baseweb="select"] *{{color:{TXT}!important;-webkit-text-fill-color:{TXT}!important;}}
div[data-baseweb="select"] svg{{fill:{LB}!important;}}
span[data-tag], span[data-baseweb="tag"]{{background-color:{MID}!important;border:1px solid {GOLD}!important;}}
span[data-tag], span[data-tag] *, span[data-baseweb="tag"] *{{color:#ffffff!important;-webkit-text-fill-color:#ffffff!important;font-weight:700}}
ul[role="listbox"]{{background:{CARD}!important;}}
ul[role="listbox"] li{{color:{TXT}!important;-webkit-text-fill-color:{TXT}!important;}}
ul[role="listbox"] li:hover, ul[role="listbox"] li[aria-selected="true"]{{background:{MID}!important;}}
button[data-testid="stNumberInputStepDown"], button[data-testid="stNumberInputStepUp"]{{background:{MID}!important;color:{TXT}!important;}}
label, label p, div[data-testid="stWidgetLabel"] p{{color:{LB}!important;-webkit-text-fill-color:{LB}!important;font-weight:600}}
div[data-testid="stCaptionContainer"] p{{color:{MUTED}!important;-webkit-text-fill-color:{MUTED}!important}}
h1,h2,h3,h4{{color:{TXT}!important}}
div[data-testid="stMarkdownContainer"] p, div[data-testid="stMarkdownContainer"] li{{color:{TXT};}}
[role="tab"], [role="tab"] *{{color:{LB}!important;-webkit-text-fill-color:{LB}!important;font-weight:600}}
[role="tab"][aria-selected="true"], [role="tab"][aria-selected="true"] *{{color:{GOLD}!important;-webkit-text-fill-color:{GOLD}!important}}
div[data-baseweb="tab-highlight"]{{background:{GOLD}!important}}
button[data-testid="stBaseButton-primary"], button[kind="primary"]{{background:{GOLD}!important;border:1px solid {GOLD}!important;}}
button[data-testid="stBaseButton-primary"] *, button[kind="primary"] *{{color:{BLUE}!important;-webkit-text-fill-color:{BLUE}!important;font-weight:800}}
button[data-testid="stBaseButton-secondary"], button[kind="secondary"]{{background:{MID}!important;border:1px solid {GOLD}!important;}}
button[data-testid="stBaseButton-secondary"] *, button[kind="secondary"] *{{color:#ffffff!important;-webkit-text-fill-color:#ffffff!important;font-weight:700}}
div[data-testid="stAlert"]{{background:{CARD}!important;border:1px solid {GOLD}!important;}}
div[data-testid="stAlert"] p, div[data-testid="stAlert"] div{{color:{TXT}!important;-webkit-text-fill-color:{TXT}!important;}}
details summary p{{color:{GOLD}!important;-webkit-text-fill-color:{GOLD}!important;font-weight:700}}
div[data-testid="stExpander"] details{{background:{CARD};border:1px solid {MID};}}
div[role="radiogroup"] p{{color:{TXT}!important;-webkit-text-fill-color:{TXT}!important}}
div[data-testid="stSliderTickBarMin"], div[data-testid="stSliderTickBarMax"], div[data-testid="stThumbValue"]{{color:{GOLD}!important}}
</style>""")


# ---------------- helpers ----------------
def t(text, color=TXT, size=15, weight=400, extra=""):
    return (f'<span style="color:{color};-webkit-text-fill-color:{color};font-size:{size}px;'
            f'font-weight:{weight};{extra}">{text}</span>')


def card(inner, border=MID, pad="14px 18px"):
    return (f'<div style="background:{CARD};border:1px solid {border};border-radius:12px;padding:{pad};'
            f'user-select:none;-webkit-user-select:none;height:100%">{inner}</div>')


def kpis(items):
    cols = st.columns(len(items))
    for c_, (h, v, s) in zip(cols, items):
        c_.html(card(t(h.upper(), GOLD, 11, 800, "letter-spacing:1px") + "<br>" + t(v, TXT, 22, 800) + "<br>" + t(s, MUTED, 12)))


def explain(title, rows, note=None):
    """Teaching box: formula, worked example with the latest numbers, how to read it."""
    body = ""
    for label, formula, example, read in rows:
        body += (f'<div style="border-left:4px solid {GOLD};padding:10px 14px;margin:0 0 14px;background:rgba(0,51,102,.35);border-radius:6px">'
                 + t(label, GOLD, 15, 800) + "<br>"
                 + t(formula, TXT, 16, 700, "font-family:Georgia,serif") + "<br>"
                 + (t("Example: " + example, LB, 14) + "<br>" if example else "")
                 + t(read, TXT, 14) + "</div>")
    if note:
        body += t(note, MUTED, 13)
    with st.expander(f"📘 {title}"):
        st.html(card(body))


IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def _stamp6(key):
    return dt.datetime.now(IST)


@st.cache_data(ttl=12 * 3600, show_spinner=False)
def _stamp12(key):
    return dt.datetime.now(IST)


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def _stamp24(key):
    return dt.datetime.now(IST)


def provenance(source, freq, latest, retrieved, note=None):
    """One line under each dataset: where it came from, how often it is observed, latest point, when it was fetched."""
    lat = latest if isinstance(latest, str) else (latest.strftime("%d %b %Y") if latest is not None else "–")
    txt = (f"<b>Source:</b> {source} &nbsp;·&nbsp; <b>Frequency:</b> {freq} &nbsp;·&nbsp; <b>Latest observation:</b> {lat}"
           f" &nbsp;·&nbsp; <b>Retrieved:</b> {retrieved.strftime('%d %b %Y, %H:%M IST')}")
    if note:
        txt += f" &nbsp;·&nbsp; {note}"
    st.html(f'<div style="border-left:3px solid {GOLD};background:rgba(17,34,64,.7);padding:7px 12px;margin:6px 0 10px;'
            f'border-radius:6px;user-select:none;-webkit-user-select:none">{t(txt, LB, 13)}</div>')


def fig_base(title, h=420):
    f = go.Figure()
    f.update_layout(title=dict(text=title, font=dict(color=TXT)), paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(17,34,64,.6)", font=dict(color=TXT), height=h,
                    legend=dict(orientation="h", y=-0.18, font=dict(color=TXT)), margin=dict(l=20, r=20, t=50, b=20),
                    hovermode="x unified")
    f.update_xaxes(gridcolor="rgba(255,255,255,.08)")
    f.update_yaxes(gridcolor="rgba(255,255,255,.08)")
    return f


def register(name, series, unit, source):
    """Keep every loaded series so the Analysis tab can use it."""
    if series is None or len(series.dropna()) == 0:
        return
    st.session_state.setdefault("datasets", {})[name] = {"s": series.dropna().astype(float), "unit": unit, "source": source}


def resample(df, freq, how="last"):
    if freq == "Daily":
        return df
    rule = {"Weekly": "W-FRI", "Monthly": "ME", "Quarterly": "QE", "Annual": "YE"}[freq]
    r = df.resample(rule)
    return (r.last() if how == "last" else r.mean()).dropna(how="all")


def downloads(df, name, key):
    a, b = st.columns(2)
    a.download_button("Download CSV", df.to_csv().encode(), f"{name}.csv", "text/csv", key=f"csv_{key}", width="stretch")
    b.download_button("Download Excel", to_excel({name[:31]: df}), f"{name}.xlsx",
                      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"xl_{key}", width="stretch")


def to_excel(sheets, notes=None):
    from openpyxl.styles import Font, PatternFill, Alignment
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for name, df in sheets.items():
            df.to_excel(xw, sheet_name=name[:31], startrow=3)
            ws = xw.sheets[name[:31]]
            ws["A1"] = name; ws["A1"].font = Font(name="Arial", size=14, bold=True, color="FFFFFF")
            ws["A2"] = f"The Mountain Path Academy · {SITE} · downloaded {dt.date.today().isoformat()}" + (f" · {notes}" if notes else "")
            ws["A2"].font = Font(name="Arial", size=9, italic=True, color="5A6B85")
            for c_ in range(1, len(df.columns) + 2):
                ws.cell(1, c_).fill = PatternFill("solid", fgColor="003366")
                h = ws.cell(4, c_); h.font = Font(name="Arial", bold=True, color="FFFFFF")
                h.fill = PatternFill("solid", fgColor="003366"); h.alignment = Alignment(horizontal="center", wrap_text=True)
                ws.column_dimensions[ws.cell(4, c_).column_letter].width = 14 if c_ > 1 else 13
            for row in ws.iter_rows(min_row=5, min_col=2):
                for c_ in row:
                    if isinstance(c_.value, float):
                        c_.number_format = "#,##0.00"
            for row in ws.iter_rows(min_row=5, max_col=1):
                for c_ in row:
                    c_.number_format = "yyyy-mm-dd"
            ws.freeze_panes = "B5"
    return buf.getvalue()


# ---------------- data sources ----------------
@st.cache_data(ttl=12 * 3600, show_spinner=False)
def treasury_year(year):
    """Daily par yield curve, one calendar year, from the US Treasury (official, public domain)."""
    u = (f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{year}/all"
         f"?type=daily_treasury_yield_curve&field_tdr_date_value={year}&page&_format=csv")
    r = requests.get(u, headers=UA, timeout=30)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    df["Date"] = pd.to_datetime(df["Date"])
    return df.set_index("Date").sort_index()


def treasury(y0, y1):
    frames, failed = [], []
    for y in range(y0, y1 + 1):
        try:
            frames.append(treasury_year(y))
        except Exception:
            failed.append(y)
    if not frames:
        return None, failed
    df = pd.concat(frames).sort_index()
    df = df[~df.index.duplicated()]
    keep = ["1 Mo", "2 Mo", "3 Mo", "4 Mo", "6 Mo", "1 Yr", "2 Yr", "3 Yr", "5 Yr", "7 Yr", "10 Yr", "20 Yr", "30 Yr"]
    return df[[c for c in keep if c in df.columns]].astype(float), failed


TENOR_YRS = {"1 Mo": 1 / 12, "2 Mo": 2 / 12, "3 Mo": .25, "4 Mo": 4 / 12, "6 Mo": .5, "1 Yr": 1, "2 Yr": 2, "3 Yr": 3,
             "5 Yr": 5, "7 Yr": 7, "10 Yr": 10, "20 Yr": 20, "30 Yr": 30}


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def ccil_curve():
    """CCIL tenor-wise indicative yields: T-bills, G-Secs and SDLs (published daily)."""
    h = requests.get("https://www.ccilindia.com/tenorwise-indicative-yields", headers=UA, timeout=25).text
    cells = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", h, re.S)]
    rows = []
    for i in range(0, len(cells) - 3, 4):
        d, bucket, sec, y = cells[i:i + 4]
        try:
            y = float(y)
        except ValueError:
            continue
        nums = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*[YD]", bucket)]
        yrs = (max(nums) / 365 if "D" in bucket else max(nums)) if nums else None
        kind = "T-bill" if "DTB" in sec else ("G-Sec" if " GS " in f" {sec} " else "SDL")
        rows.append({"Date": d[:10], "Tenor": bucket, "Years": round(yrs, 2) if yrs else None, "Security": sec,
                     "Type": kind, "YTM %": y})
    if not rows:
        raise RuntimeError("CCIL table not found")  # not cached
    return pd.DataFrame(rows)


def fred_key():
    """FRED API key from Streamlit secrets (FRED_API_KEY) or the environment. Never shown in the app."""
    import os
    try:
        k = st.secrets.get("FRED_API_KEY")
    except Exception:
        k = None
    return k or os.environ.get("FRED_API_KEY")


@st.cache_data(ttl=12 * 3600, show_spinner=False)
def _fred_api(series_id, key):
    r = requests.get("https://api.stlouisfed.org/fred/series/observations",
                     params={"series_id": series_id, "api_key": key, "file_type": "json"}, timeout=30)
    r.raise_for_status()
    obs = r.json()["observations"]
    s = pd.Series({pd.Timestamp(o["date"]): o["value"] for o in obs})
    return pd.to_numeric(s, errors="coerce").dropna().rename(series_id)


@st.cache_data(ttl=12 * 3600, show_spinner=False)
def _fred_csv(series_id):
    r = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv", params={"id": series_id}, headers=UA, timeout=30)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = ["Date", series_id]
    df["Date"] = pd.to_datetime(df["Date"])
    return pd.to_numeric(df.set_index("Date")[series_id], errors="coerce").dropna()


def fred(series_id):
    """FRED: official API when a key is configured, else the public CSV (no key)."""
    key = fred_key()
    if key:
        try:
            return _fred_api(series_id, key)
        except Exception:
            pass
    return _fred_csv(series_id)


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def yahoo_close(symbol, period="10y"):
    import time
    import yfinance as yf
    h = None
    for i_ in range(3):  # Yahoo often sends cloud servers an empty reply: retry, and never cache an empty result
        try:
            h = yf.Ticker(symbol).history(period=period, interval="1d", auto_adjust=True)
            if h is not None and not h.empty:
                break
        except Exception:
            pass
        time.sleep(1.5 * (i_ + 1))
    if h is None or h.empty:
        raise RuntimeError(f"No prices for {symbol}")
    s = h["Close"].astype(float)
    s.index = pd.to_datetime(s.index).tz_localize(None)
    return s


WB_IND = {"GDP (current US$, billions)": ("NY.GDP.MKTP.CD", 1e9), "GDP growth (annual %)": ("NY.GDP.MKTP.KD.ZG", 1),
          "GDP per capita (current US$)": ("NY.GDP.PCAP.CD", 1), "GDP (constant 2015 US$, billions)": ("NY.GDP.MKTP.KD", 1e9),
          "Inflation, consumer prices (annual %)": ("FP.CPI.TOTL.ZG", 1), "Unemployment (% of labour force)": ("SL.UEM.TOTL.ZS", 1),
          "Gross capital formation (% of GDP)": ("NE.GDI.TOTL.ZS", 1), "Exports of goods & services (% of GDP)": ("NE.EXP.GNFS.ZS", 1),
          "Population (millions)": ("SP.POP.TOTL", 1e6), "Central government debt (% of GDP)": ("GC.DOD.TOTL.GD.ZS", 1)}
COUNTRIES = {"India": "IND", "United States": "USA", "China": "CHN", "Japan": "JPN", "Germany": "DEU", "United Kingdom": "GBR",
             "France": "FRA", "Brazil": "BRA", "Indonesia": "IDN", "Russia": "RUS", "South Africa": "ZAF", "Mexico": "MEX",
             "Korea": "KOR", "Australia": "AUS", "Canada": "CAN", "Saudi Arabia": "SAU", "Bangladesh": "BGD",
             "Sri Lanka": "LKA", "Vietnam": "VNM", "World": "WLD"}
IMF_IND = {"Real GDP growth (%)": "NGDP_RPCH", "GDP, current prices (US$ billions)": "NGDPD",
           "GDP per capita (US$)": "NGDPDPC", "Inflation (average CPI, %)": "PCPIPCH",
           "Unemployment rate (%)": "LUR", "Govt gross debt (% of GDP)": "GGXWDG_NGDP"}


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def world_bank(code, iso3):
    r = requests.get(f"https://api.worldbank.org/v2/country/{iso3}/indicator/{code}",
                     params={"format": "json", "per_page": 200}, headers=UA, timeout=30)
    r.raise_for_status()
    js = r.json()
    if len(js) < 2 or not js[1]:
        return None
    s = pd.Series({int(d["date"]): d["value"] for d in js[1] if d["value"] is not None}, dtype=float).sort_index()
    return s


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def imf(code):
    r = requests.get(f"https://www.imf.org/external/datamapper/api/v1/{code}", timeout=40)  # IMF blocks browser-like UAs
    r.raise_for_status()
    return r.json().get("values", {}).get(code, {})


# ---------------- page header ----------------
st.html(card(t("FREE DATA LAB · MBA · CFA · FRM", BLUE, 12, 800,
               f"background:{GOLD};-webkit-text-fill-color:{BLUE};padding:4px 10px;border-radius:5px;letter-spacing:1px") +
             "<br><br>" + t("Markets & Macro Data Lab", TXT, 34, 800) + "<br>" +
             t("Yield curves, credit spreads, bond indices and GDP data from official sources. Load, chart, download, "
               "then analyse and forecast in the Analysis tab.", LB, 16), pad="22px 26px"))

tabs = st.tabs(["🇺🇸 US Treasury yields", "🇮🇳 India G-Sec yields", "💳 Credit & spreads", "📊 Bond markets",
                "🌍 GDP & macro", "📈 Analysis & forecasting"])

# ---------------- US Treasury ----------------
with tabs[0]:
    st.caption("Daily par yield curve from the US Department of the Treasury (official, public domain), 1990 onwards.")
    this_year = dt.date.today().year
    a, b, c = st.columns([2, 2, 1])
    yr = a.slider("Years", 1990, this_year, (this_year - 5, this_year), key="ust_years")
    tenors = b.multiselect("Tenors", list(TENOR_YRS), ["3 Mo", "2 Yr", "10 Yr", "30 Yr"], key="ust_ten")
    freq = c.selectbox("Frequency", ["Daily", "Weekly", "Monthly", "Quarterly", "Annual"], index=2, key="ust_freq")
    if st.button("Load US Treasury yields", type="primary", key="ust_go"):
        with st.spinner("Downloading from the US Treasury…"):
            st.session_state["ust"] = treasury(*yr)
    res = st.session_state.get("ust")
    if res:
        df, failed = res
        if failed:
            st.warning(f"Years not loaded: {failed}. Try again later.")
        if df is not None and len(df):
            last = df.dropna(how="all").iloc[-1]
            d0 = df.dropna(how="all").index[-1]
            s10_2 = last.get("10 Yr") - last.get("2 Yr") if "10 Yr" in last and "2 Yr" in last else None
            s10_3m = last.get("10 Yr") - last.get("3 Mo") if "10 Yr" in last and "3 Mo" in last else None
            provenance("U.S. Department of the Treasury, daily par yield curve (official)",
                       f"daily (business days); shown {freq.lower()}", d0, _stamp12(f"ust{yr}"),
                       "end-of-day rates, not intraday quotes")
            kpis([("10-yr yield", f"{last.get('10 Yr', float('nan')):.2f}%", f"on {d0.date()}"),
                  ("2-yr yield", f"{last.get('2 Yr', float('nan')):.2f}%", ""),
                  ("10y − 2y spread", f"{s10_2*100:+.0f} bp" if s10_2 is not None else "–", "negative = inverted"),
                  ("10y − 3m spread", f"{s10_3m*100:+.0f} bp" if s10_3m is not None else "–", "recession signal if negative")])
            a, b = st.columns(2)
            f = fig_base("Yield curve: latest vs 1 month and 1 year earlier")
            for lab, when, colr in [("Latest", d0, GOLD), ("1 month ago", d0 - pd.DateOffset(months=1), LB),
                                    ("1 year ago", d0 - pd.DateOffset(years=1), MUTED)]:
                sub = df[df.index <= when].dropna(how="all")
                if len(sub):
                    row = sub.iloc[-1].dropna()
                    f.add_scatter(x=[TENOR_YRS[k] for k in row.index], y=row.values, mode="lines+markers",
                                  name=f"{lab} ({sub.index[-1].date()})", line=dict(color=colr, width=3))
            f.update_xaxes(title="Maturity (years)", type="log", tickvals=[.25, .5, 1, 2, 5, 10, 20, 30],
                           ticktext=["3m", "6m", "1y", "2y", "5y", "10y", "20y", "30y"])
            f.update_yaxes(title="Yield %")
            a.plotly_chart(f, width="stretch")
            view = resample(df[tenors] if tenors else df, freq)
            f = fig_base(f"{freq} yields")
            for i_, c_ in enumerate(view.columns):
                f.add_scatter(x=view.index, y=view[c_], name=c_, line=dict(color=PALETTE[i_ % 10], width=2))
            f.update_yaxes(title="Yield %")
            b.plotly_chart(f, width="stretch")
            sp = pd.DataFrame({"10y − 2y (bp)": (df["10 Yr"] - df["2 Yr"]) * 100,
                               "10y − 3m (bp)": (df["10 Yr"] - df["3 Mo"]) * 100}).dropna()
            sp = resample(sp, freq)
            f = fig_base(f"Term spreads ({freq.lower()})", 340)
            f.add_scatter(x=sp.index, y=sp["10y − 2y (bp)"], name="10y − 2y", line=dict(color=GOLD, width=2))
            f.add_scatter(x=sp.index, y=sp["10y − 3m (bp)"], name="10y − 3m", line=dict(color=LB, width=2))
            f.add_hline(y=0, line=dict(color=RED, dash="dot"))
            st.plotly_chart(f, width="stretch")
            for c_ in view.columns:
                register(f"US Treasury {c_} ({freq.lower()})", view[c_], "%", "US Treasury")
            register(f"US 10y−2y spread bp ({freq.lower()})", sp["10y − 2y (bp)"], "bp", "US Treasury")
            y10_, y2_, y3m_ = last.get("10 Yr"), last.get("2 Yr"), last.get("3 Mo")
            explain("How the term spreads are calculated", [
                ("10-year minus 2-year spread", "Spread (bp) = (10-yr yield − 2-yr yield) × 100",
                 f"({y10_:.2f}% − {y2_:.2f}%) × 100 = {(y10_ - y2_) * 100:+.0f} bp on {d0.date()}" if y10_ == y10_ and y2_ == y2_ else None,
                 "Positive = normal, upward-sloping curve: investors want more yield to lend for longer. "
                 "Negative = inverted curve: markets expect the Fed to cut rates, usually because growth is expected to slow. "
                 "Every US recession since the 1970s was preceded by a 10y–2y inversion, though with a long and variable lag (often 6–24 months)."),
                ("10-year minus 3-month spread", "Spread (bp) = (10-yr yield − 3-month T-bill yield) × 100",
                 f"({y10_:.2f}% − {y3m_:.2f}%) × 100 = {(y10_ - y3m_) * 100:+.0f} bp" if y10_ == y10_ and y3m_ == y3m_ else None,
                 "The 3-month bill tracks the Fed funds rate closely, so this spread compares long-term rates with today's policy rate. "
                 "It is the version the New York Fed uses in its recession-probability model."),
                ("Why multiply by 100?", "1 percentage point = 100 basis points (bp);  1 bp = 0.01%",
                 "a move from 4.10% to 4.35% is +25 bp", "Spreads are quoted in basis points because the differences are small."),
            ], note="Yields are US Treasury par yields (bond-equivalent, semi-annual). With a lower frequency (weekly, monthly) "
                    "the spread uses the last observation of each period.")
            out = view.join(sp, how="left")
            with st.expander(f"Data table ({len(out)} rows)"):
                st.dataframe(out.tail(300), width="stretch")
            downloads(out, f"US_Treasury_{freq}_{yr[0]}_{yr[1]}", "ust")
    else:
        st.html(card(t("Choose years, tenors and frequency, then click <b>Load US Treasury yields</b>. "
                       "Each year is one download, kept for 12 hours.", TXT, 14)))

# ---------------- India G-Sec ----------------
with tabs[1]:
    st.caption("Today's curve: CCIL tenor-wise indicative yields (T-bills, G-Secs, SDLs). History: 10-year and 3-month "
               "rates, monthly, from FRED (OECD/RBI series).")
    try:
        cc = ccil_curve()
    except Exception as e:
        cc = None
        st.warning(f"CCIL yields could not be loaded right now ({str(e)[:80]}).")
    if cc is not None and len(cc):
        g = cc[cc["Type"].isin(["T-bill", "G-Sec"])].sort_values("Years")
        sdl = cc[cc["Type"] == "SDL"].sort_values("Years")
        def ylookup(n):
            r_ = g.iloc[(g["Years"] - n).abs().argsort()[:1]]
            return float(r_["YTM %"].iloc[0]) if len(r_) else None
        y10, y91, y2 = ylookup(10), ylookup(0.25), ylookup(2)
        provenance("CCIL tenor-wise indicative yields", "daily snapshot (one date)", str(pd.Timestamp(cc['Date'].iloc[0]).strftime('%d %b %Y')),
                   _stamp6("ccil"), "indicative end-of-day yields")
        kpis([("10-yr G-Sec", f"{y10:.2f}%", f"on {cc['Date'].iloc[0]}"), ("91-day T-bill", f"{y91:.2f}%", ""),
              ("10y − 91d spread", f"{(y10 - y91)*100:+.0f} bp", "term premium"),
              ("10y SDL − G-Sec", f"{(float(sdl[sdl['Years'] == 10]['YTM %'].iloc[0]) - y10)*100:+.0f} bp"
               if len(sdl[sdl["Years"] == 10]) else "–", "state borrowing premium")])
        a, b = st.columns([3, 2])
        f = fig_base("India yield curve today (CCIL indicative)")
        f.add_scatter(x=g["Years"], y=g["YTM %"], mode="lines+markers+text", name="T-bills & G-Secs",
                      text=[f"{v:.2f}" for v in g["YTM %"]], textposition="top center", line=dict(color=GOLD, width=3))
        if len(sdl):
            f.add_scatter(x=sdl["Years"], y=sdl["YTM %"], mode="markers", name="State loans (SDL)",
                          marker=dict(color=LB, size=11, symbol="diamond"))
        f.update_xaxes(title="Maturity (years)"); f.update_yaxes(title="YTM %")
        a.plotly_chart(f, width="stretch")
        b.dataframe(cc.drop(columns=["Date"]).set_index("Tenor"), width="stretch", height=420)
        sdl10_ = sdl[sdl["Years"] == 10]["YTM %"]
        sdl10_ = float(sdl10_.iloc[0]) if len(sdl10_) else None
        explain("How the India spreads are calculated", [
            ("Term spread: 10-year G-Sec minus 91-day T-bill", "Spread (bp) = (10-yr G-Sec YTM − 91-day T-bill yield) × 100",
             f"({y10:.2f}% − {y91:.2f}%) × 100 = {(y10 - y91) * 100:+.0f} bp",
             "The 91-day T-bill sits close to the RBI's policy and overnight rates; the 10-year carries expectations of future rates "
             "plus a term premium. A wide positive spread = steep curve (rate cuts already done or long-term inflation/supply worries); "
             "a narrow or negative spread = tight money today, easing expected."),
            ("State borrowing premium: 10-year SDL minus 10-year G-Sec", "Spread (bp) = (10-yr SDL YTM − 10-yr G-Sec YTM) × 100",
             f"({sdl10_:.2f}% − {y10:.2f}%) × 100 = {(sdl10_ - y10) * 100:+.0f} bp" if sdl10_ else None,
             "State Development Loans (SDLs) are borrowings by state governments. They carry no default history but are less liquid "
             "and have a smaller investor base than central-government G-Secs, so they pay extra yield. The spread widens when states "
             "borrow heavily (often in Q4 of the financial year) and narrows when demand from banks and insurers is strong."),
            ("Reading tenor buckets", "Tenor '9Y-10Y' = CCIL's benchmark bond maturing in 9–10 years; plotted at the upper bound (10 yrs)",
             None, "T-bills are plotted at 0.25, 0.5 and 1 year (91, 182 and 364 days ÷ 365)."),
        ], note="All yields are CCIL indicative yields (annualised YTM, semi-annual compounding for G-Secs and SDLs; T-bills on a "
                "discount-to-yield basis). Spreads between different bond types are approximate when the maturities differ slightly.")
        downloads(cc.set_index("Date"), "India_GSec_curve_CCIL", "ccil")
        st.caption("Source: CCIL tenor-wise indicative yields. CCIL does not authorise commercial use of its website data "
                   "without written permission; shown here for education with attribution.")
    st.markdown("#### History (monthly)")
    if st.button("Load India rate history (FRED)", key="ind_hist_go"):
        out, bad = {}, []
        for sid, lab in [("INDIRLTLT01STM", "India 10-yr G-Sec yield %"), ("INDIR3TIB01STM", "India 3-month T-bill %"),
                         ("IRLTLT01USM156N", "US 10-yr yield %")]:
            try:
                out[lab] = fred(sid)
            except Exception:
                bad.append(lab)
        st.session_state["ind_hist"] = (pd.DataFrame(out), bad)
    if st.session_state.get("ind_hist"):
        hd, bad = st.session_state["ind_hist"]
        if bad:
            st.warning(f"Not loaded (FRED unavailable): {', '.join(bad)}")
        if len(hd.columns):
            hd = hd[hd.index >= "2000-01-01"]
            if {"India 10-yr G-Sec yield %", "US 10-yr yield %"} <= set(hd.columns):
                hd["India − US 10y spread (bp)"] = (hd["India 10-yr G-Sec yield %"] - hd["US 10-yr yield %"]) * 100
            provenance("FRED (OECD Main Economic Indicators)", "monthly averages", hd.dropna(how="all").index[-1],
                       _stamp12("indhist"), "published with a lag of one to three months")
            f = fig_base("India rates since 2000 (monthly)")
            for i_, c_ in enumerate([c for c in hd.columns if "bp" not in c]):
                f.add_scatter(x=hd.index, y=hd[c_], name=c_, line=dict(color=PALETTE[i_], width=2))
            st.plotly_chart(f, width="stretch")
            for c_ in hd.columns:
                register(f"{c_} (monthly)", hd[c_], "bp" if "bp" in c_ else "%", "FRED")
            if "India − US 10y spread (bp)" in hd:
                sp_ = hd["India − US 10y spread (bp)"].dropna()
                iv, uv = hd["India 10-yr G-Sec yield %"].dropna(), hd["US 10-yr yield %"].dropna()
                explain("How the India − US spread is calculated", [
                    ("India − US 10-year yield spread", "Spread (bp) = (India 10-yr G-Sec yield − US 10-yr Treasury yield) × 100",
                     f"({iv.iloc[-1]:.2f}% − {uv.iloc[-1]:.2f}%) × 100 = {sp_.iloc[-1]:+.0f} bp ({sp_.index[-1]:%b %Y})" if len(sp_) else None,
                     "The extra yield a foreign investor earns in Indian government bonds over US Treasuries, before currency moves. "
                     "It mostly reflects the inflation gap (expected rupee depreciation) plus a country-risk premium. "
                     "A narrowing spread makes Indian bonds less attractive to foreign investors unless the rupee is expected to stay stable."),
                    ("Currency-adjusted view", "Return in US$ ≈ India yield − expected rupee depreciation",
                     "a 280 bp spread with 3% expected depreciation leaves about −20 bp for an unhedged US investor",
                     "This is uncovered interest parity: the spread is only a gain if the rupee depreciates by less than the spread."),
                ], note="Monthly averages from FRED (OECD Main Economic Indicators). For the daily India–US spread use the RBI spread app.")
            downloads(hd, "India_rates_monthly_FRED", "indh")
            st.caption("For the daily India–US 10-year spread, see the RBI spread app on the Financial Data page.")

# ---------------- credit & spreads ----------------
with tabs[2]:
    st.caption("US credit spreads (ICE BofA option-adjusted spreads) and term spreads from FRED, daily.")
    opts = {"US investment-grade corporate OAS (%)": "BAMLC0A0CM", "US high-yield corporate OAS (%)": "BAMLH0A0HYM2",
            "US BBB corporate OAS (%)": "BAMLC0A4CBBB", "10y − 2y Treasury spread (%)": "T10Y2Y",
            "10y − 3m Treasury spread (%)": "T10Y3M", "10-yr breakeven inflation (%)": "T10YIE",
            "10-yr TIPS real yield (%)": "DFII10", "Fed funds effective rate (%)": "DFF", "SOFR (%)": "SOFR"}
    a, b, c = st.columns([3, 1, 1])
    pick = a.multiselect("Series", list(opts), list(opts)[:2] + ["10y − 2y Treasury spread (%)"], key="cr_pick")
    since = b.number_input("From year", 1990, this_year, this_year - 10, key="cr_from")
    cfreq = c.selectbox("Frequency", ["Daily", "Weekly", "Monthly"], index=1, key="cr_freq")
    if st.button("Load spreads (FRED)", type="primary", key="cr_go"):
        out, bad = {}, []
        with st.spinner("Downloading from FRED…"):
            for lab in pick:
                try:
                    out[lab] = fred(opts[lab])
                except Exception:
                    bad.append(lab)
        st.session_state["cr"] = (pd.DataFrame(out), bad)
    if st.session_state.get("cr"):
        cd, bad = st.session_state["cr"]
        if bad:
            st.warning(f"Not loaded (FRED unavailable right now): {', '.join(bad)}")
        if len(cd.columns):
            cd = resample(cd[cd.index >= f"{since}-01-01"], cfreq)
            provenance("FRED (ICE BofA indices, U.S. Treasury, Federal Reserve)", f"daily; shown {cfreq.lower()}",
                       cd.dropna(how="all").index[-1], _stamp12("cr" + "|".join(cd.columns)), "end-of-day values")
            kpis([(c_[:28], f"{cd[c_].dropna().iloc[-1]:.2f}", f"latest, {cd[c_].dropna().index[-1].date()}") for c_ in cd.columns[:4]])
            f = fig_base(f"Spreads and rates ({cfreq.lower()})")
            for i_, c_ in enumerate(cd.columns):
                f.add_scatter(x=cd.index, y=cd[c_], name=c_, line=dict(color=PALETTE[i_ % 10], width=2))
            st.plotly_chart(f, width="stretch")
            for c_ in cd.columns:
                register(f"{c_} ({cfreq.lower()})", cd[c_], "%", "FRED / ICE BofA")
            def lastv(lab):
                return cd[lab].dropna().iloc[-1] if lab in cd and len(cd[lab].dropna()) else None
            ig_, hy_, bbb_ = lastv("US investment-grade corporate OAS (%)"), lastv("US high-yield corporate OAS (%)"), lastv("US BBB corporate OAS (%)")
            be_, real_ = lastv("10-yr breakeven inflation (%)"), lastv("10-yr TIPS real yield (%)")
            explain("How the credit spreads and related rates are calculated", [
                ("Option-adjusted spread (OAS)", "OAS = corporate bond yield − Treasury yield of matching maturity − value of embedded options",
                 (f"investment grade {ig_:.2f}% = {ig_*100:.0f} bp" + (f";  high yield {hy_:.2f}% = {hy_*100:.0f} bp" if hy_ else "")) if ig_ else None,
                 "The extra yield investors demand for default risk and lower liquidity. ICE BofA computes it for every bond in the index "
                 "(the spread over the Treasury curve that discounts the bond's cash flows to its price, after removing call/put option value) "
                 "and averages by market value. Spreads widen in stress (2008: HY above 19%; March 2020: about 11%) and tighten in calm, "
                 "risk-on markets."),
                ("High-yield minus investment-grade", "HY − IG differential (bp) = (HY OAS − IG OAS) × 100",
                 f"({hy_:.2f}% − {ig_:.2f}%) × 100 = {(hy_ - ig_) * 100:.0f} bp" if hy_ and ig_ else None,
                 "Measures the extra reward for moving down the credit ladder into junk-rated bonds; a rising gap signals growing "
                 "concern about defaults among weaker companies."),
                ("BBB spread", "BBB OAS = spread on the lowest investment-grade rating",
                 f"{bbb_:.2f}% = {bbb_*100:.0f} bp" if bbb_ else None,
                 "Watched closely because a downgrade from BBB to BB ('fallen angel') forces many funds to sell."),
                ("Breakeven inflation", "Breakeven = nominal 10-yr Treasury yield − 10-yr TIPS real yield",
                 f"breakeven {be_:.2f}% with real yield {real_:.2f}% → nominal ≈ {be_ + real_:.2f}%" if be_ and real_ else None,
                 "The average inflation rate at which a regular Treasury and an inflation-protected TIPS give the same return: "
                 "the market's inflation expectation (plus a small risk and liquidity premium)."),
                ("Term spreads on this tab", "10y − 2y and 10y − 3m are published by FRED in percentage points",
                 None, "Multiply by 100 for basis points. See the US Treasury tab for the full explanation."),
            ], note="OAS series are in percent, so 1.00 = 100 bp. Source: ICE BofA indices via FRED.")
            downloads(cd, f"US_spreads_{cfreq}", "cr")
            st.caption("OAS series: ICE BofA indices via FRED. Check FRED's notes for each series' licence.")
    else:
        st.html(card(t("Pick series and click <b>Load spreads</b>.", TXT, 14)))

# ---------------- bond markets ----------------
with tabs[3]:
    st.caption("Bond market performance from tradable indices and ETFs (Yahoo Finance, total-return proxies).")
    BONDS = {"US 1–3y Treasuries (SHY)": "SHY", "US 7–10y Treasuries (IEF)": "IEF", "US 20y+ Treasuries (TLT)": "TLT",
             "US aggregate bonds (AGG)": "AGG", "US investment-grade corporates (LQD)": "LQD",
             "US high-yield corporates (HYG)": "HYG", "US TIPS (TIP)": "TIP", "Emerging-market bonds (EMB)": "EMB",
             "India Nifty G-Sec 10Y index": "NIFTYGS10YR.NS", "India Nifty G-Sec 15Y+ index": "NIFTYGS15YRPLUS.NS"}
    a, b = st.columns([4, 1])
    bsel = a.multiselect("Bond indices / ETFs", list(BONDS), ["US 7–10y Treasuries (IEF)", "US investment-grade corporates (LQD)",
                                                              "US high-yield corporates (HYG)", "India Nifty G-Sec 10Y index"], key="bm_sel")
    per = b.selectbox("History", ["1y", "3y", "5y", "10y"], index=2, key="bm_per")
    if st.button("Load bond markets", type="primary", key="bm_go"):
        out, bad = {}, []
        with st.spinner("Downloading prices…"):
            for lab in bsel:
                try:
                    s_ = yahoo_close(BONDS[lab], per)
                    if s_ is not None:
                        out[lab] = s_
                    else:
                        bad.append(lab)
                except Exception:
                    bad.append(lab)
        st.session_state["bm"] = (pd.DataFrame(out), bad)
    if st.session_state.get("bm"):
        bd, bad = st.session_state["bm"]
        if bad:
            st.warning(f"Not loaded: {', '.join(bad)}")
        if len(bd.columns):
            bd = bd.ffill()
            def ret(s_, days):
                s_ = s_.dropna(); past = s_[s_.index <= s_.index[-1] - pd.Timedelta(days=days)]
                return s_.iloc[-1] / past.iloc[-1] - 1 if len(past) else np.nan
            tbl = pd.DataFrame({lab: {"1 month": ret(bd[lab], 30), "3 months": ret(bd[lab], 91), "1 year": ret(bd[lab], 365),
                                      "3 years (total)": ret(bd[lab], 1095),
                                      "Volatility (ann.)": bd[lab].pct_change().std() * np.sqrt(252)} for lab in bd.columns}).T
            provenance("Yahoo Finance (ETF and index closing prices, adjusted for distributions)", "daily closes",
                       bd.dropna(how="all").index[-1], _stamp6("bm" + "|".join(bd.columns)),
                       "may be delayed; not a real-time feed")
            st.dataframe(tbl.map(lambda v: "–" if pd.isna(v) else f"{v*100:+.1f}%" if v == v else "–"), width="stretch")
            f = fig_base("Growth of 100")
            for i_, c_ in enumerate(bd.columns):
                s_ = bd[c_].dropna()
                f.add_scatter(x=s_.index, y=s_ / s_.iloc[0] * 100, name=c_, line=dict(color=PALETTE[i_ % 10], width=2))
            st.plotly_chart(f, width="stretch")
            for c_ in bd.columns:
                register(f"{c_} price (daily)", bd[c_], "index", "Yahoo Finance")
            downloads(bd, f"Bond_markets_{per}", "bm")
    else:
        st.html(card(t("Pick indices and click <b>Load bond markets</b>.", TXT, 14)))

# ---------------- GDP & macro ----------------
with tabs[4]:
    src = st.radio("Source", ["World Bank (history, annual)", "IMF World Economic Outlook (history + projections)"],
                   horizontal=True, key="mac_src")
    a, b = st.columns([2, 3])
    if src.startswith("World Bank"):
        ind = a.selectbox("Indicator", list(WB_IND), key="wb_ind")
        ctry = b.multiselect("Countries", list(COUNTRIES), ["India", "United States", "China", "Japan", "Germany"], key="wb_c")
        if st.button("Load World Bank data", type="primary", key="wb_go"):
            code, scale = WB_IND[ind]
            out, bad = {}, []
            with st.spinner("Downloading from the World Bank…"):
                for c_ in ctry:
                    try:
                        s_ = world_bank(code, COUNTRIES[c_])
                        if s_ is not None:
                            out[c_] = s_ / scale
                        else:
                            bad.append(c_)
                    except Exception:
                        bad.append(c_)
            st.session_state["mac"] = (pd.DataFrame(out), bad, ind, "World Bank WDI")
    else:
        ind = a.selectbox("Indicator", list(IMF_IND), key="imf_ind")
        ctry = b.multiselect("Countries", list(COUNTRIES), ["India", "United States", "China", "World"], key="imf_c")
        if st.button("Load IMF data", type="primary", key="imf_go"):
            out, bad = {}, []
            with st.spinner("Downloading from the IMF…"):
                try:
                    vals = imf(IMF_IND[ind])
                except Exception:
                    vals = {}
                for c_ in ctry:
                    k_ = "WEOWORLD" if c_ == "World" else COUNTRIES[c_]
                    if k_ in vals:
                        out[c_] = pd.Series({int(y): float(v) for y, v in vals[k_].items() if v is not None}).sort_index()
                    else:
                        bad.append(c_)
            st.session_state["mac"] = (pd.DataFrame(out), bad, ind, "IMF WEO")
    if st.session_state.get("mac"):
        md, bad, ind_, src_ = st.session_state["mac"]
        if bad:
            st.warning(f"Not available: {', '.join(bad)}")
        if len(md.columns):
            md.index.name = "Year"
            proj_from = dt.date.today().year if src_ == "IMF WEO" else None
            _last_actual = (proj_from - 1) if proj_from else int(md.dropna(how="all").index.max())
            provenance("World Bank World Development Indicators" if src_ != "IMF WEO" else "IMF World Economic Outlook (DataMapper)",
                       "annual", f"{_last_actual}" + (f" (projections to {int(md.index.max())})" if proj_from else ""),
                       _stamp24("mac" + ind_ + "|".join(md.columns)),
                       "IMF values after the last actual year are projections" if proj_from else "latest year varies by country")
            f = fig_base(f"{ind_} ({src_})")
            for i_, c_ in enumerate(md.columns):
                s_ = md[c_].dropna()
                f.add_scatter(x=s_.index, y=s_.values, name=c_, line=dict(color=PALETTE[i_ % 10], width=3))
            if proj_from:
                f.add_vrect(x0=proj_from - .5, x1=md.index.max() + .5, fillcolor=GOLD, opacity=.08, line_width=0,
                            annotation_text="IMF projections", annotation_font_color=GOLD)
            st.plotly_chart(f, width="stretch")
            last = md.ffill().iloc[-1] if proj_from is None else md.loc[md.index <= proj_from - 1].ffill().iloc[-1]
            st.dataframe(md.sort_index(ascending=False).head(40).T, width="stretch")
            for c_ in md.columns:
                register(f"{c_}: {ind_} ({src_}, annual)", md[c_].dropna().rename(lambda y: pd.Timestamp(year=int(y), month=12, day=31)),
                         ind_, src_)
            downloads(md, f"{src_.split()[0]}_{IMF_IND.get(ind_, WB_IND.get(ind_, ('x',))[0])}", "mac")
            st.caption("World Bank WDI and IMF WEO data are free to use with attribution. IMF values after the last "
                       "actual year are projections.")
    else:
        st.html(card(t("Pick an indicator and countries, then load. GDP growth, GDP level, per-capita GDP and inflation "
                       "are ready-made series for trend and time-series forecasting.", TXT, 14)))

# ---------------- analysis & forecasting ----------------
with tabs[5]:
    ds = st.session_state.get("datasets", {})
    if not ds:
        st.html(card(t("Load data in any tab first; every series appears here for analysis.", TXT, 15)))
    else:
        a, b = st.columns([3, 1])
        name = a.selectbox("Series", list(ds), key="an_series")
        transform = b.selectbox("Transform", ["Level", "Change (Δ)", "% change", "Log"], key="an_tr")
        s = ds[name]["s"].copy()
        if transform == "Change (Δ)":
            s = s.diff().dropna()
        elif transform == "% change":
            s = (s.pct_change() * 100).dropna()
        elif transform == "Log":
            s = np.log(s[s > 0])
        n = len(s)
        span_y = (s.index[-1] - s.index[0]).days / 365.25 if n > 1 else 0
        unit_ = ds[name]["unit"]
        s0_, s1_ = ds[name]["s"].iloc[0], ds[name]["s"].iloc[-1]
        cagr = None
        if not ("%" in unit_ or unit_ == "bp") and span_y > 0 and s0_ > 0 and s1_ > 0:
            cagr = (s1_ / s0_) ** (1 / span_y) - 1
        ac1 = s.autocorr(1) if n > 3 else np.nan
        kpis([("Observations", f"{n}", f"{s.index[0].date()} → {s.index[-1].date()}"), ("Mean", f"{s.mean():,.3f}", f"sd {s.std():,.3f}"),
              ("Min / max", f"{s.min():,.2f} / {s.max():,.2f}", ""), ("Lag-1 autocorrelation", f"{ac1:.2f}", "near 1 = persistent"),
              ("Growth (CAGR)", f"{cagr*100:.2f}%" if cagr is not None and transform == "Level" else "–", "levels only (not rates)")])

        st.markdown("#### Forecast")
        a, b, c = st.columns(3)
        method = a.selectbox("Method", ["Linear trend (OLS on time)", "Log-linear trend (constant growth)",
                                        "AR(1) on the series", "Holt's linear exponential smoothing", "Moving average (naive)"], key="an_m")
        h_ = b.number_input("Periods ahead", 1, 60, 5, key="an_h")
        win = c.number_input("Use last N observations (0 = all)", 0, 10000, 0, key="an_win")
        y = s.iloc[-win:] if win else s
        y = y.dropna()
        tt = np.arange(len(y), dtype=float)
        idx = y.index
        fq = pd.infer_freq(idx[-12:]) if len(idx) >= 3 else None
        if fq is None:
            gap = (idx[-1] - idx[-2]).days if len(idx) > 1 else 1
            fq = "YE" if gap > 300 else "QE" if gap > 80 else "ME" if gap > 25 else "W-FRI" if gap > 5 else "B"
        fut_idx = pd.date_range(idx[-1], periods=int(h_) + 1, freq=fq)[1:]
        fc, lo, hi, eq, fitted, band_note = None, None, None, "", None, ""
        try:
            if method.startswith("Log-linear") and (y <= 0).any():
                raise ValueError("the log-linear trend needs strictly positive values (this series has zeros or negatives). "
                                 "Use the linear trend, or a level series such as GDP in US$")
            if method.startswith("Linear trend") or method.startswith("Log-linear"):
                logm = method.startswith("Log")
                yy = np.log(y.values) if logm else y.values
                X = np.column_stack([np.ones(len(tt)), tt])
                beta_, res_, *_ = np.linalg.lstsq(X, yy, rcond=None)
                fit = X @ beta_; resid = yy - fit
                se = np.sqrt(resid @ resid / max(len(yy) - 2, 1))
                r2 = 1 - (resid @ resid) / (((yy - yy.mean()) ** 2).sum() or 1)
                tf = np.arange(len(y), len(y) + int(h_))
                xtx = np.linalg.inv(X.T @ X)
                sef = np.array([se * np.sqrt(1 + np.array([1, k]) @ xtx @ np.array([1, k])) for k in tf])
                m_ = beta_[0] + beta_[1] * tf
                fc, lo, hi = m_, m_ - 1.96 * sef, m_ + 1.96 * sef
                fitted = pd.Series(np.exp(fit) if logm else fit, index=y.index)
                band_note = ("95% prediction band from the regression: assumes independent, normally distributed residuals with "
                             "constant variance, and that the straight-line trend continues; includes uncertainty in the fitted line.")
                if logm:
                    fc, lo, hi = np.exp(fc), np.exp(lo), np.exp(hi)
                    eq = f"ln(y) = {beta_[0]:.4f} + {beta_[1]:.5f}·t   →   growth ≈ {np.expm1(beta_[1])*100:.2f}% per period;  R² = {r2:.3f}"
                else:
                    eq = f"y = {beta_[0]:.4f} + {beta_[1]:.5f}·t   (t = 0, 1, 2, …);  R² = {r2:.3f};  s.e. = {se:.4f}"
            elif method.startswith("AR(1)"):
                x0, x1 = y.values[:-1], y.values[1:]
                X = np.column_stack([np.ones(len(x0)), x0])
                (cst, phi), *_ = np.linalg.lstsq(X, x1, rcond=None)
                resid = x1 - (cst + phi * x0); se = np.sqrt(resid @ resid / max(len(x1) - 2, 1))
                fc, last_ = [], y.values[-1]
                for k in range(int(h_)):
                    last_ = cst + phi * last_; fc.append(last_)
                fc = np.array(fc)
                var = np.array([se ** 2 * sum(phi ** (2 * j) for j in range(k + 1)) for k in range(int(h_))])
                lo, hi = fc - 1.96 * np.sqrt(var), fc + 1.96 * np.sqrt(var)
                mean_lr = cst / (1 - phi) if abs(phi) < 1 else float("nan")
                fitted = pd.Series(cst + phi * x0, index=y.index[1:])
                band_note = ("95% band from the AR(1) error variance compounded over the horizon: assumes normal, uncorrelated shocks "
                             "and stable parameters; parameter-estimation uncertainty is not included, so the band is too narrow.")
                eq = (f"y(t) = {cst:.4f} + {phi:.4f}·y(t−1) + e;   long-run mean = {mean_lr:.3f}" +
                      ("   (φ ≥ 1: non-stationary, try the Change transform)" if phi >= 1 else ""))
            elif method.startswith("Holt"):
                from statsmodels.tsa.holtwinters import ExponentialSmoothing
                mdl = ExponentialSmoothing(y.values, trend="add", initialization_method="estimated").fit()
                fc = mdl.forecast(int(h_)); se = np.std(mdl.resid, ddof=1)
                lo, hi = fc - 1.96 * se * np.sqrt(np.arange(1, int(h_) + 1)), fc + 1.96 * se * np.sqrt(np.arange(1, int(h_) + 1))
                eq = f"α (level) = {mdl.params['smoothing_level']:.3f},  β (trend) = {mdl.params['smoothing_trend']:.3f}"
                fitted = pd.Series(mdl.fittedvalues, index=y.index)
                band_note = ("Approximate 95% band: one-step error × √h. A rule of thumb that assumes normal, independent errors; "
                             "it is not the exact Holt prediction interval.")
            else:
                k_ = min(12, len(y))
                m_ = y.iloc[-k_:].mean(); se = y.iloc[-k_:].std()
                fc = np.repeat(m_, int(h_)); lo, hi = fc - 1.96 * se, fc + 1.96 * se
                eq = f"Forecast = average of the last {k_} observations = {m_:.4f}"
                band_note = (f"95% band = average ± 1.96 × standard deviation of the last {k_} observations; it does not widen "
                             "with the horizon, so it understates uncertainty further out.")
        except Exception as e:
            st.error(f"Forecast failed: {e}")
        f = fig_base(f"{name} — {transform.lower()}: observed, fitted and forecast", 460)
        f.add_scatter(x=y.index, y=y.values, name="Observed (data)", line=dict(color=LB, width=2))
        if fitted is not None:
            f.add_scatter(x=fitted.index, y=fitted.values, name="Fitted (in-sample)", line=dict(color="#ff9f43", width=1.6, dash="dot"))
        f.add_vline(x=y.index[-1], line=dict(color=MUTED, dash="dot"))
        if fc is not None:
            f.add_scatter(x=fut_idx, y=hi, mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip")
            f.add_scatter(x=fut_idx, y=lo, mode="lines", fill="tonexty", fillcolor="rgba(255,215,0,.15)", line=dict(width=0), name="95% band")
            f.add_scatter(x=fut_idx, y=fc, name="Forecast (out-of-sample)", line=dict(color=GOLD, width=3, dash="dash"))
        st.plotly_chart(f, width="stretch")
        if eq:
            st.html(card(t("MODEL", GOLD, 11, 800, "letter-spacing:1px") + "<br>" + t(eq, TXT, 16, 700) +
                         (("<br><br>" + t("FORECAST BAND ASSUMPTIONS", GOLD, 11, 800, "letter-spacing:1px") + "<br>" + t(band_note, TXT, 14))
                          if band_note else ""), border=GOLD))
        st.caption("Observed = the downloaded data. Fitted = the model's in-sample values (how well it explains the past). "
                   "Forecast = out-of-sample projection to the right of the dotted line; it is a model output, not data.")
        if fc is not None:
            ft = pd.DataFrame({"Forecast": fc, "Lower 95%": lo, "Upper 95%": hi}, index=fut_idx)
            ft.index.name = "Period"
            ft.index = ft.index.date
            a, b = st.columns([2, 3])
            a.dataframe(ft.style.format("{:,.3f}"), width="stretch")
            with b:
                st.markdown("**Diagnostics**")
                if n > 12:
                    lags = range(1, min(13, n // 2))
                    acf = [s.autocorr(L) for L in lags]
                    f2 = fig_base("Autocorrelation (ACF)", 260)
                    f2.add_bar(x=list(lags), y=acf, marker_color=MID, name="ACF")
                    f2.add_hline(y=1.96 / np.sqrt(n), line=dict(color=GOLD, dash="dot"))
                    f2.add_hline(y=-1.96 / np.sqrt(n), line=dict(color=GOLD, dash="dot"))
                    st.plotly_chart(f2, width="stretch")
                try:
                    from statsmodels.tsa.stattools import adfuller
                    if n > 15:
                        adf = adfuller(s.values, autolag="AIC")
                        st.caption(f"ADF test: statistic {adf[0]:.2f}, p-value {adf[1]:.3f} → "
                                   + ("stationary at 5%" if adf[1] < 0.05 else "not stationary at 5% (consider the Change transform)"))
                except Exception:
                    pass
            obs_ = y.rename("Observed").to_frame()
            if fitted is not None:
                obs_["Fitted (in-sample)"] = fitted
            ft.index = pd.to_datetime(ft.index)
            full = pd.concat([obs_, ft.rename(columns={"Forecast": "Forecast (out-of-sample)"})])
            downloads(full, f"Forecast_{re.sub(r'[^A-Za-z0-9]+', '_', name)[:40]}", "fc")
        with st.expander("Download all loaded series (one Excel file)"):
            all_ = {re.sub(r"[\[\]:*?/\\]", "", k)[:31]: v["s"].to_frame("value") for k, v in ds.items()}
            st.download_button("Download all series (Excel)", to_excel(all_), "MPA_data_lab_series.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
        st.caption("Teaching models: simple, transparent forecasts. Trends assume the past pattern continues; "
                   "AR(1) and Holt adapt to recent values. Not investment or policy advice.")

with st.sidebar:
    st.html(card(t("THE MOUNTAIN PATH ACADEMY", GOLD, 12, 800, "letter-spacing:1.5px") + "<br>" +
                 t("Markets & Macro Data Lab", TXT, 18, 700)))
    st.caption("Every series you load is added to the Analysis tab automatically.")
    loaded = st.session_state.get("datasets", {})
    st.html(card(t("SERIES READY FOR ANALYSIS", GOLD, 11, 800, "letter-spacing:1px") + "<br>" +
                 t(str(len(loaded)), TXT, 22, 800) + "<br>" +
                 t("<br>".join((k[:38] + ("…" if len(k) > 38 else "")) for k in list(loaded)[-8:]) + ("<br>…" if len(loaded) > 8 else "") if loaded else "None yet: load data in any tab.", MUTED, 12)))
    if loaded and st.button("Clear loaded series", width="stretch"):
        st.session_state["datasets"] = {}
        st.rerun()
    st.caption(("FRED: API key active." if fred_key() else "FRED: public download (no key).") + " Sources: US Treasury · CCIL · FRED · Yahoo Finance · World Bank · IMF WEO. Education only.")


# ---------------- footer ----------------
st.html(f"""<div style="margin-top:28px;padding:16px 10px;border-top:2px solid {GOLD};text-align:center;user-select:none;-webkit-user-select:none">
{t("The Mountain Path Academy · Prof. V. Ravichandran", TXT, 14, 700)}<br>
<a href="{SITE}" target="_blank" style="color:{GOLD};-webkit-text-fill-color:{GOLD};text-decoration:none;font-weight:700">{SITE}</a>
{t(" · ", MUTED)}<a href="https://www.linkedin.com/in/trichyravis" target="_blank" style="color:{GOLD};-webkit-text-fill-color:{GOLD};text-decoration:none;font-weight:700">LinkedIn</a>
{t(" · ", MUTED)}<a href="https://github.com/trichyravis" target="_blank" style="color:{GOLD};-webkit-text-fill-color:{GOLD};text-decoration:none;font-weight:700">GitHub</a><br>
{t("Data: US Treasury · CCIL · FRED · Yahoo Finance · World Bank · IMF. Education only — not investment advice.", MUTED, 12)}</div>""")
