from fastapi import FastAPI
from pydantic import BaseModel
import pennylane as qml
from pennylane import numpy as np
import pandas as pd
import yfinance as yf
from alpha_vantage.timeseries import TimeSeries

# Define FastAPI app
app = FastAPI()
API_KEY = " TA1CE0GTYSNKF0PE"
stocks = ["AAPL", "GOOGL", "MSFT", "TSLA"]

# Quantum Device Setup
n_assets = 4  # Default, will update dynamically
dev = qml.device("default.qubit", wires=n_assets)

# Define Request Model
class PortfolioRequest(BaseModel):
    symbols: list  # List of stock symbols
    period: str = "6mo"  # Default period for historical data

def get_stock_data(symbol):
    ts = TimeSeries(key=API_KEY, output_format="pandas")
    data, meta = ts.get_daily(symbol=symbol, outputsize="compact")
    return data["4. close"]

# Get data for all stocks
portfolio_data = {stock: get_stock_data(stock) for stock in stocks}

# Convert to DataFrame
df = pd.DataFrame(portfolio_data)
df = df.pct_change().dropna()  # Compute daily returns
print(df.head())

def qaoa_layer(gamma, beta):
    """Apply a single layer of QAOA"""
    for i in range(n_assets):
        qml.RX(2 * beta, wires=i)
    for i in range(n_assets):
        for j in range(i + 1, n_assets):
            qml.CNOT(wires=[i, j])
            qml.RZ(2 * gamma * Q[i, j], wires=j)
            qml.CNOT(wires=[i, j])

@qml.qnode(dev)
def circuit(gamma, beta):
    """QAOA circuit"""
    qaoa_layer(gamma, beta)
    return qml.probs(wires=range(n_assets))

@app.post("/optimize-hedging/")
def optimize_hedging(request: PortfolioRequest):
    global n_assets, dev, Q
    
    # Fetch market data
    returns, cov_matrix = fetch_market_data(request.symbols, request.period)
    n_assets = len(request.symbols)
    dev = qml.device("default.qubit", wires=n_assets)

    # Define QUBO matrix
    gamma_factor = 0.1  # Risk penalty factor
    Q = cov_matrix - gamma_factor * np.outer(returns, returns)

    # Train QAOA
    gamma, beta = np.array(0.5, requires_grad=True), np.array(0.5, requires_grad=True)
    opt = qml.GradientDescentOptimizer(stepsize=0.1)
    for _ in range(50):  # Train for 50 steps
        gamma, beta = opt.step(lambda v: -circuit(v[0], v[1])[0], [gamma, beta])

    # Get optimized hedge allocation
    optimal_weights = circuit(gamma, beta).tolist()

    return {"symbols": request.symbols, "weights": optimal_weights}
