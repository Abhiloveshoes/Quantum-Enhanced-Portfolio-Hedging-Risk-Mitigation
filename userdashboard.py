import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# FastAPI Backend URL
API_URL = "http://127.0.0.1:8000/optimize-hedging/"

st.title("🔬 Quantum Portfolio Hedging Optimizer")

# User Inputs
symbols = st.text_input("Enter stock symbols (comma-separated):", "AAPL, MSFT, TSLA, AMZN")
symbol_list = [s.strip().upper() for s in symbols.split(",")]

if st.button("Optimize Hedge"):
    st.write("📡 Fetching data and running quantum optimization...")

    try:
        # Call FastAPI backend
        response = requests.post(API_URL, json={"symbols": symbol_list})
        response.raise_for_status()  # Raise an error for failed requests

        result = response.json()
        weights = result.get("weights", [])[0]
        
        if not weights:
            st.error("⚠️ No optimization results received. Check input symbols.")
            st.stop()

        # Display Results
        df = pd.DataFrame({"Stock": result["symbols"], "Weight": weights})
        
        col1, col2 = st.columns(2)

        with col1:
            fig_bar = px.bar(df, x="Stock", y="Weight", title="Optimal Hedge Allocation", text="Weight")
            st.plotly_chart(fig_bar)

        with col2:
            fig_pie = px.pie(df, names="Stock", values="Weight", title="Portfolio Distribution")
            st.plotly_chart(fig_pie)

        # Portfolio Insights
        expected_return = sum(df["Weight"] * 0.02)  # Assume 2% average return per asset
        risk = sum(df["Weight"]**2)  # Simple risk measure (variance)

        st.subheader("📊 Portfolio Insights")
        st.write(f"✅ **Expected Return:** {expected_return:.2%}")
        st.write(f"⚠️ **Risk Estimate (Variance):** {risk:.4f}")

    except requests.exceptions.RequestException as e:
        st.error(f"❌ API Request Failed: {e}")

    except Exception as e:
        st.error(f"⚠️ Unexpected Error: {e}")
