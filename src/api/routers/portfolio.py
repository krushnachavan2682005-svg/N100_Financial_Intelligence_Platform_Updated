import os
import pandas as pd
from fastapi import APIRouter

router = APIRouter()


@router.get("/portfolio/stats")
def get_portfolio_stats():
    path = "output/portfolio_stats.csv"
    if not os.path.exists(path):
        return [
            {
                "metric": "roe",
                "p10": 5,
                "p25": 10,
                "p50": 15,
                "p75": 20,
                "p90": 25,
                "mean": 15,
                "std": 5,
            }
        ]

    df = pd.read_csv(path)
    return df.to_dict(orient="records")
