import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# FastAPI Backend URL (Replace with Render Deployment URL)
API_URL = "https://api.render.com/deploy/srv-cven59nnoe9s73eq361g?key=e28PSyX8hWk"

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
    st.write("API Response:", result)  # 🔍 Debugging: Show full API response

    if "weights" in result:
        weights = result["weights"]
        df = pd.DataFrame({"Stock": result["symbols"], "Weight": weights})
        fig = px.bar(df, x="Stock", y="Weight", title="Optimal Hedge Allocation", text="Weight")
        st.plotly_chart(fig)
    else:
        st.error("Error: 'weights' key not found in API response.")
else:
    st.error(f"API Error {response.status_code}: {response.text}")

    

