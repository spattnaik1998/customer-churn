"""
Customer Churn Prediction API

FastAPI application for serving churn prediction model.
"""

from fastapi import FastAPI

app = FastAPI(
    title="Customer Churn Prediction API",
    description="API for predicting customer churn using machine learning",
    version="1.0.0"
)


@app.get("/health")
async def health_check():
    """Health check endpoint to verify API is running."""
    return {"status": "ok"}