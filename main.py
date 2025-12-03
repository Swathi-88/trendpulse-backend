from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pytrends.request import TrendReq
import pandas as pd
from typing import List
import time

app = FastAPI(
    title="TrendPulse AI",
    description="Analyze Google Trends data with AI-powered insights",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    keyword: str


class AnalyzeResponse(BaseModel):
    trend: str
    score: int
    confidence: str
    related_keywords: List[str]
    best_posting_time: str
    graph_data: List[int]


cache = {}

def get_pytrend():
    return TrendReq(
        hl='en-US',
        tz=330,
        requests_args={'headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}}
    )

pytrend = get_pytrend()


def fetch_trends_data(keyword: str, max_retries: int = 3):
    global pytrend
    for attempt in range(max_retries):
        try:
            time.sleep(2)
            pytrend.build_payload([keyword], timeframe='now 7-d')
            data = pytrend.interest_over_time()
            return data
        except Exception as e:
            if '429' in str(e) and attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10
                time.sleep(wait_time)
                pytrend = get_pytrend()
                continue
            raise
    return None


def clean_data(data, keyword: str) -> List[int]:
    if data is None or data.empty:
        return []
    
    if 'isPartial' in data.columns:
        data = data.drop(columns=['isPartial'])
    
    values = data[keyword].tolist()
    last_7 = values[-7:] if len(values) >= 7 else values
    
    return [int(v) for v in last_7]


def calculate_slope(data_points: List[int]) -> float:
    n = len(data_points)
    if n < 2:
        return 0.0
    
    x = list(range(n))
    y = data_points
    
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(x[i] * y[i] for i in range(n))
    sum_x_squared = sum(xi ** 2 for xi in x)
    
    denominator = n * sum_x_squared - sum_x ** 2
    if denominator == 0:
        return 0.0
    
    m = (n * sum_xy - sum_x * sum_y) / denominator
    return m


def classify_trend(slope: float) -> str:
    if slope > 0.8:
        return "Rising"
    elif slope < -0.8:
        return "Declining"
    else:
        return "Stable"


def calculate_score(slope: float) -> int:
    score = slope * 12 + 50
    score = max(0, min(100, score))
    return round(score)


def determine_confidence(slope: float) -> str:
    abs_slope = abs(slope)
    if abs_slope > 1.2:
        return "High"
    elif abs_slope > 0.6:
        return "Medium"
    else:
        return "Low"


def get_best_posting_time(trend: str) -> str:
    posting_times = {
        "Rising": "7 PM – 10 PM",
        "Stable": "12 PM – 3 PM",
        "Declining": "9 AM – 12 PM"
    }
    return posting_times.get(trend, "12 PM – 3 PM")


def fetch_related_keywords(keyword: str, limit: int = 3) -> List[str]:
    try:
        time.sleep(1)
        suggestions = pytrend.suggestions(keyword=keyword)
        
        related = []
        for suggestion in suggestions[:limit]:
            if 'title' in suggestion:
                related.append(suggestion['title'])
        
        return related
    except Exception:
        return []


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    keyword = request.keyword.strip().lower()
    
    if not keyword:
        raise HTTPException(status_code=400, detail="Keyword cannot be empty")
    
    if keyword in cache:
        return cache[keyword]
    
    try:
        raw_data = fetch_trends_data(keyword)
        
        if raw_data is None or raw_data.empty:
            raise HTTPException(
                status_code=404, 
                detail=f"No trend data found for keyword: {keyword}"
            )
        
        graph_data = clean_data(raw_data, keyword)
        
        if len(graph_data) < 2:
            raise HTTPException(
                status_code=400, 
                detail="Insufficient data points for analysis"
            )
        
        slope = calculate_slope(graph_data)
        trend = classify_trend(slope)
        score = calculate_score(slope)
        confidence = determine_confidence(slope)
        best_posting_time = get_best_posting_time(trend)
        related_keywords = fetch_related_keywords(keyword)
        
        response = {
            "trend": trend,
            "score": score,
            "confidence": confidence,
            "related_keywords": related_keywords,
            "best_posting_time": best_posting_time,
            "graph_data": graph_data
        }
        
        cache[keyword] = response
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        if '429' in error_msg:
            raise HTTPException(
                status_code=429, 
                detail="Google Trends rate limit reached. Please try again in a few minutes."
            )
        raise HTTPException(
            status_code=500, 
            detail=f"Error analyzing keyword: {error_msg}"
        )


@app.get("/")
def root():
    return {
        "name": "TrendPulse AI",
        "version": "1.0.0",
        "description": "Analyze Google Trends data with AI-powered insights",
        "endpoints": {
            "POST /analyze": "Analyze a keyword for trend data"
        }
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
