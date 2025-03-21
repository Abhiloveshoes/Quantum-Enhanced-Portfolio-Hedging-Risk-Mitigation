import pandas as pd
import numpy as np
from alpha_vantage.timeseries import TimeSeries


API_KEY = " TA1CE0GTYSNKF0PE"

# List of portfolio stocks
stocks = ["AAPL", "GOOGL", "MSFT", "TSLA"]


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

import pennylane as qml
from pennylane import numpy as np
import cvxpy as cp

# Load market data (from previous step)
returns = df.mean().values  # Mean daily returns
cov_matrix = df.cov().values  # Covariance matrix

# Define Quantum QUBO Parameters
n_assets = len(returns)
gamma = 0.1  # Risk penalty factor
target_return = 0.001  # Minimum return threshold

# Create QUBO matrix
Q = cov_matrix - gamma * np.outer(returns, returns)

# Quantum Circuit for QAOA
dev = qml.device("default.qubit", wires=n_assets)

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

gamma = np.array([0.5], requires_grad=True)
beta = np.array([0.5], requires_grad=True)


# Classical optimizer
opt = qml.GradientDescentOptimizer(stepsize=0.1)
steps = 50
gamma, beta = np.array([0.5]), np.array([0.5])

# Train QAOA to find optimal hedge weights
for _ in range(steps):
   gamma, beta = opt.step(lambda v: -circuit(v[0], v[1])[0], [gamma, beta])

# Get optimal portfolio hedge allocation
optimal_weights = circuit(gamma, beta)
print("Optimal Hedging Weights:", optimal_weights)
