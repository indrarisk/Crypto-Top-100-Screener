import requests
import pandas as pd
import streamlit as st

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

import yfinance as yf

# ================= STREAMLIT CONFIG =================
st.set_page_config(page_title="Market Radar", layout="wide")
st.title("📊 Market Radar")
st.caption("Crypto + US Stocks | AI Momentum Screener")

# ================= US STOCK LIST =================
US_STOCKS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META",
    "GOOGL", "TSLA", "AMD", "NFLX", "INTC",
    "COIN", "PLTR", "SHOP", "SNOW",
    "JPM", "BAC", "XOM", "CVX",
    "SPY", "QQQ"
]

# ================= CRYPTO DATA =================
@st.cache_data(ttl=120)
def get_top_100_crypto():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "price_change_percentage": "24h"
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return pd.DataFrame(r.json())

# ================= US STOCK DATA =================
@st.cache_data(ttl=300)
def get_us_stocks(tickers):
    data = []

    for t in tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.fast_info

            price = info.get("lastPrice")
            prev = info.get("previousClose")
            volume = info.get("volume")

            if price and prev:
                change = (price - prev) / prev * 100
            else:
                change = None

            data.append({
                "Symbol": t,
                "Price (USD)": price,
                "Change (%)": change,
                "Volume": volume
            })

        except Exception:
            continue

    return pd.DataFrame(data)

# ================= TABS =================
tab1, tab2 = st.tabs(["🪙 Crypto", "🇺🇸 US Stocks"])

# ================= CRYPTO TAB =================
with tab1:
    st.subheader("🪙 Crypto AI Momentum Screener")

    try:
        df = get_top_100_crypto()

        df = df[[
            "market_cap_rank",
            "name",
            "symbol",
            "current_price",
            "price_change_percentage_24h",
            "total_volume"
        ]]

        df.columns = [
            "Rank",
            "Coin",
            "Symbol",
            "Price (USD)",
            "24h Change (%)",
            "Volume"
        ]

        min_change = st.slider(
            "Minimal % perubahan harga (24h)",
            min_value=0.0,
            max_value=20.0,
            value=2.0,
            step=0.5
        )

        df["Volume_Score"] = df["Volume"] / df["Volume"].max()
        df["Rank_Score"] = 1 / df["Rank"]

        df["Score"] = (
            df["24h Change (%)"] * 0.5 +
            df["Volume_Score"] * 30 +
            df["Rank_Score"] * 10
        )

        filtered = df[
            (df["Volume"] > 50_000_000) &
            (df["24h Change (%)"] >= min_change)
        ].copy()

        if len(filtered) >= 3:
            features = filtered[[
                "24h Change (%)",
                "Volume",
                "Rank",
                "Score"
            ]]

            scaled = StandardScaler().fit_transform(features)

            kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
            filtered["Cluster"] = kmeans.fit_predict(scaled)

            cluster_score = (
                filtered.groupby("Cluster")["Score"]
                .mean()
                .sort_values(ascending=False)
            )

            best_cluster = cluster_score.index[0]

            filtered["AI_Label"] = filtered["Cluster"].apply(
                lambda x: "🟢 Potensi Momentum"
                if x == best_cluster else "⚪ Netral"
            )
        else:
            filtered["AI_Label"] = "⚪ Data Kurang"

        st.dataframe(
            filtered[
                filtered["AI_Label"] == "🟢 Potensi Momentum"
            ][[
                "Rank",
                "Coin",
                "Symbol",
                "Price (USD)",
                "24h Change (%)",
                "Volume",
                "Score",
                "AI_Label"
            ]].head(10),
            width="stretch"
        )

    except Exception as e:
        st.error(f"Error crypto: {e}")

# ================= US STOCK TAB + AI =================
with tab2:
    st.subheader("🇺🇸 US Stock AI Momentum Screener")

    stock_df = get_us_stocks(US_STOCKS)

    if stock_df.empty:
        st.warning("Data saham belum tersedia.")
    else:
        stock_df = stock_df.dropna()

        # ===== SCORE SYSTEM SAHAM =====
        stock_df["Volume_Score"] = stock_df["Volume"] / stock_df["Volume"].max()
        stock_df["Score"] = (
            stock_df["Change (%)"] * 0.6 +
            stock_df["Volume_Score"] * 40
        )

        if len(stock_df) >= 3:
            features = stock_df[[
                "Change (%)",
                "Volume",
                "Score"
            ]]

            scaled = StandardScaler().fit_transform(features)

            kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
            stock_df["Cluster"] = kmeans.fit_predict(scaled)

            cluster_score = (
                stock_df.groupby("Cluster")["Score"]
                .mean()
                .sort_values(ascending=False)
            )

            best_cluster = cluster_score.index[0]

            stock_df["AI_Label"] = stock_df["Cluster"].apply(
                lambda x: "🟢 Momentum Saham"
                if x == best_cluster else "⚪ Netral"
            )
        else:
            stock_df["AI_Label"] = "⚪ Data Kurang"

        st.dataframe(
            stock_df[
                stock_df["AI_Label"] == "🟢 Momentum Saham"
            ].sort_values("Score", ascending=False),
            width="stretch"
        )

    st.caption("Data via Yahoo Finance (delay ±15 menit)")
