import requests
import pandas as pd
import streamlit as st
import time

st.set_page_config(page_title="Crypto Market Screener", layout="wide")

st.title("📊 Crypto Market Screener")
st.caption("Top 100 Coin | Ranking Score | Alert Otomatis")

@st.cache_data(ttl=60)
def get_top_100():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "price_change_percentage": "24h"
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return pd.DataFrame(response.json())

try:
    # ================= DATA =================
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

    # ================= FILTER =================
    st.subheader("⚙️ Filter Market")

    min_change = st.slider(
        "Minimal % perubahan harga (24h)",
        min_value=0.0,
        max_value=20.0,
        value=2.0,
        step=0.5
    )

    min_score = st.slider(
        "Minimal Score untuk Alert",
        min_value=0.0,
        max_value=50.0,
        value=15.0,
        step=1.0
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

    # ================= TABLE =================
    st.subheader("🏆 Top Ranked Coin Sekarang")
    st.caption("Top 10 berdasarkan score | Slider = filter tambahan")

    st.dataframe(
        filtered[[
            "Rank",
            "Coin",
            "Symbol",
            "Price (USD)",
            "24h Change (%)",
            "Volume",
            "Score"
        ]].head(10),
        use_container_width=True
    )

    # ================= ALERT =================
    alerts = filtered[filtered["Score"] >= min_score]

    st.subheader("🚨 Market Alert")

    if not alerts.empty:
        st.error("🚨 ALERT! Coin dengan peluang tinggi terdeteksi")

        for _, row in alerts.iterrows():
            st.markdown(
                f"""
                **{row['Coin']} ({row['Symbol'].upper()})**  
                💰 Price: ${row['Price (USD)']:.2f}  
                📈 24h Change: {row['24h Change (%)']:.2f}%  
                🧮 Score: {row['Score']:.2f}
                ---
                """
            )
    else:
        st.success("✅ Tidak ada alert — market relatif tenang")

except Exception as e:
    st.error(f"❌ Error ambil data: {e}")

st.caption("🔄 Auto refresh setiap 60 detik")
time.sleep(60)
st.rerun()

