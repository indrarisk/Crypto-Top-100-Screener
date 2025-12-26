import requests
import pandas as pd
import streamlit as st
import time

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# ================= STREAMLIT CONFIG =================
st.set_page_config(page_title="Market Radar", layout="wide")
st.title("📊 Crypto Market Radar")
st.caption("Top 100 Coin | Ranking | AI/ML Clustering")

# ================= DATA SOURCE =================
@st.cache_data(ttl=120)
def get_top_100():
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

try:
    # ================= LOAD DATA =================
    df = get_top_100()

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

    # ================= USER FILTER =================
    st.subheader("⚙️ Market Filter")

    min_change = st.slider(
        "Minimal % perubahan harga (24h)",
        min_value=0.0,
        max_value=20.0,
        value=2.0,
        step=0.5
    )

    # ================= SCORE SYSTEM =================
    df["Volume_Score"] = df["Volume"] / df["Volume"].max()
    df["Rank_Score"] = 1 / df["Rank"]

    df["Score"] = (
        df["24h Change (%)"] * 0.5 +
        df["Volume_Score"] * 30 +
        df["Rank_Score"] * 10
    )

    ranked = df[df["Volume"] > 50_000_000].sort_values(
        "Score", ascending=False
    )

    filtered = ranked[ranked["24h Change (%)"] >= min_change]

    # ================= AI / ML CLUSTERING =================
    features = filtered[[
        "24h Change (%)",
        "Volume",
        "Rank",
        "Score"
    ]]

    if len(features) >= 3:
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(features)

        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        filtered["Cluster"] = kmeans.fit_predict(scaled_features)

        cluster_summary = (
            filtered.groupby("Cluster")
            .agg({
                "Score": "mean",
                "24h Change (%)": "mean",
                "Volume": "mean"
            })
            .sort_values("Score", ascending=False)
        )

        best_cluster = cluster_summary.index[0]

        filtered["AI_Label"] = filtered["Cluster"].apply(
            lambda x: "🟢 Potensi Momentum" if x == best_cluster else "⚪ Netral"
        )
    else:
        filtered["AI_Label"] = "⚪ Data Kurang"

    # ================= TABLE OUTPUT =================
    st.subheader("🤖 AI Screener — Coin dengan Potensi Momentum")

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
        use_container_width=True
    )

except Exception as e:
    st.error(f"❌ Error: {e}")

# ================= AUTO REFRESH =================
st.caption("🔄 Auto refresh setiap 120 detik")


