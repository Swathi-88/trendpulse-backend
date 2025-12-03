# TrendPulse AI

## Overview
TrendPulse AI is a FastAPI-powered backend service that analyzes Google Trends data to provide insights about keyword popularity, trend direction, and optimal posting times.

## Project Structure
```
├── main.py          # FastAPI application with trend analysis logic
├── pyproject.toml   # Python dependencies
├── .gitignore       # Git ignore patterns
└── replit.md        # Project documentation
```

## API Endpoints

### GET /
Returns API information and available endpoints.

### GET /health
Health check endpoint returning server status.

### POST /analyze
Analyzes a keyword using Google Trends data.

**Request:**
```json
{
  "keyword": "AI jobs"
}
```

**Response:**
```json
{
  "trend": "Rising|Stable|Declining",
  "score": 0-100,
  "confidence": "High|Medium|Low",
  "related_keywords": ["keyword1", "keyword2", "keyword3"],
  "best_posting_time": "7 PM – 10 PM",
  "graph_data": [int, int, ...]
}
```

## Technical Details

### Trend Analysis Logic
- Fetches 7-day Google Trends data using pytrends
- Cleans data by removing isPartial column and extracting last 7 data points
- Calculates slope using linear regression: `m = (n*Σxy - Σx*Σy) / (n*Σx² - (Σx)²)`

### Trend Classification
- Rising: slope > 0.8
- Stable: -0.8 ≤ slope ≤ 0.8
- Declining: slope < -0.8

### Score Calculation
`score = round(min(max(slope * 12 + 50, 0), 100))`

### Confidence Levels
- High: |slope| > 1.2
- Medium: 0.6 < |slope| ≤ 1.2
- Low: |slope| ≤ 0.6

### Best Posting Times
- Rising trends: 7 PM – 10 PM
- Stable trends: 12 PM – 3 PM
- Declining trends: 9 AM – 12 PM

## Dependencies
- FastAPI
- uvicorn
- pytrends
- pandas
- pydantic

## Running the Server
The server runs on port 5000 and is started via the "TrendPulse API" workflow.
