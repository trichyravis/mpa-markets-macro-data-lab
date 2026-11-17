# Markets & Macro Data Lab — The Mountain Path Academy
Downloadable series for analysis and forecasting practice:
- US Treasury par yield curve, 1990 onwards, any tenor, daily/weekly/monthly/quarterly/annual (US Treasury)
- India G-Sec / T-bill / SDL curve today (CCIL) and monthly India 10Y & 3M history (FRED)
- US credit spreads (ICE BofA OAS), term spreads, breakevens, SOFR (FRED)
- Bond index/ETF performance, US and India (Yahoo Finance)
- GDP and macro indicators for 20 economies (World Bank WDI; IMF WEO with projections)
- Analysis tab: stats, ACF, ADF test; linear, log-linear, AR(1), Holt and moving-average forecasts with 95% bands; CSV/Excel downloads

Optional: FRED API key in Streamlit secrets as FRED_API_KEY (see secrets.toml.example); without it the public FRED CSV is used.
Run locally:  pip install -r requirements.txt  &&  streamlit run app.py
Deploy: push to GitHub, then share.streamlit.io → New app → app.py.
https://themountainpathacademy.com
