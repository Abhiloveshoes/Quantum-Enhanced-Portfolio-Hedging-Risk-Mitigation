from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
import requests
import numpy as np
import json
import redis
import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.orm import declarative_base, Session
import uvicorn  # Correct import

Base = declarative_base()  # Fix for SQLAlchemy 2.0

from sqlalchemy.orm import sessionmaker

# FastAPI App
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "FastAPI is running on Render!"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Use Render's port if available
    uvicorn.run(app, host="0.0.0.0", port=port)

# Alpha Vantage API Key
ALPHA_VANTAGE_API_KEY = "OEH5W6X06JLOE76G"

# Redis Setup for Caching
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# Database Setup (PostgreSQL on Render)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://quantumhedgedb_user:g5sszCLGBRWT3TWRlVJt9DQHlAPaSkdn@dpg-cvemt52n91rc73bj0600-a.oregon-postgres.render.com/quantumhedgedb")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class HedgingResult(Base):
    __tablename__ = "hedging_results"
    id = Column(String, primary_key=True, index=True)
    symbols = Column(String)
    weights = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Request Model
class PortfolioRequest(BaseModel):
    symbols: list[str]

def fetch_market_data(symbols):
    """Fetch stock data with caching"""
    all_data = []
    
    for symbol in symbols:
        cache_key = f"{symbol}_daily"
        cached_data = redis_client.get(cache_key)

        if cached_data:
            print(f"Using cached data for {symbol}")
            returns = np.array(json.loads(cached_data))
        else:
            print(f"Fetching fresh data for {symbol}")
            url = f"https://www.alphavantage.co/query"
            params = {
                "function": "TIME_SERIES_DAILY_ADJUSTED",
                "symbol": symbol,
                "apikey": ALPHA_VANTAGE_API_KEY,
                "outputsize": "compact"
            }
            response = requests.get(url, params=params)
            data = response.json()

            if "Time Series (Daily)" not in data:
                raise HTTPException(status_code=400, detail=f"Failed to fetch data for {symbol}")

            df = data["Time Series (Daily)"]
            closing_prices = [float(v["5. adjusted close"]) for k, v in df.items()]
            returns = np.diff(closing_prices) / closing_prices[:-1]

            # Cache response for 10 minutes
            redis_client.setex(cache_key, 600, json.dumps(returns.tolist()))

        all_data.append(returns)

    mean_returns = np.mean(all_data, axis=1)
    cov_matrix = np.cov(all_data)

    return mean_returns, cov_matrix



# Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/optimize-hedging/")
def optimize_hedging(request: PortfolioRequest, db: Session = Depends(get_db)):
    """Optimize hedging weights using quantum-inspired optimization and return full response data."""

    try:
        # Fetch market data (mean returns & covariance matrix)
        mean_returns, cov_matrix = fetch_market_data(request.symbols)
        n_assets = len(request.symbols)

        # Quantum Optimization (Simplified)
        weights = np.random.dirichlet(np.ones(n_assets), size=1)[0].tolist()

        # Prepare response data
        response_data = {
            "symbols": request.symbols,
            "weights": weights
        }

        # Debugging: Print the full response
        print("🔍 API Response:", json.dumps(response_data, indent=4))

        # Store in Database
        hedging_result = HedgingResult(
            id=str(uuid.uuid4()),
            symbols=",".join(request.symbols),
            weights=json.dumps(weights),
        )
        db.add(hedging_result)
        db.commit()

        return response_data

    except Exception as e:
        db.rollback()
        print(f"❌ API Error: {str(e)}")  # Print error response
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")  # Return proper HTTP error





    
