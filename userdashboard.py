import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# FastAPI Backend URL (Replace with Render Deployment URL)
API_URL = "https://your-fastapi-app.onrender.com/optimize-hedging/"

st.title("Quantum Portfolio Hedging Optimizer")

# User Inputs
symbols = st.text_input("Enter stock symbols (comma-separated):", "AAPL, MSFT, TSLA, AMZN")
symbol_list = [s.strip().upper() for s in symbols.split(",")]

if st.button("Optimize Hedge"):
    st.write("Fetching data and running quantum optimization...")

    # Call FastAPI backend
    response = requests.post(API_URL, json={"symbols": symbol_list})
    if response.status_code == 200:
        result = response.json()
        weights = result["weights"]

        # Display Results
        df = pd.DataFrame({"Stock": result["symbols"], "Weight": weights})
        fig = px.bar(df, x="Stock", y="Weight", title="Optimal Hedge Allocation", text="Weight")
        st.plotly_chart(fig)
    else:
        st.error("Error: Could not optimize. Try again.")
