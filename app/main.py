"""
Customer Churn Prediction API

FastAPI application for serving churn prediction model.
"""

import pickle
import numpy as np
import pandas as pd
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Customer Churn Prediction API",
    description="API for predicting customer churn using machine learning",
    version="1.0.0"
)

# Global variable to store the loaded model
model_data = None


class CustomerFeatures(BaseModel):
    """Pydantic model for customer feature input."""
    age: int
    gender: str  # "Male" or "Female"
    tenure: int
    usage_frequency: int
    support_calls: int
    payment_delay: int
    subscription_type: str  # "Basic", "Premium", or "Standard"
    contract_length: str  # "Monthly", "Quarterly", or "Annual"
    total_spend: int
    last_interaction: int


class PredictionResponse(BaseModel):
    """Pydantic model for prediction response."""
    customer_id: Optional[str] = None
    churn_probability: float
    churn_prediction: int
    risk_level: str


@app.on_event("startup")
async def load_model():
    """Load the trained model at startup."""
    global model_data
    try:
        logger.info("Loading churn prediction model...")
        with open('../models/churn_model.pkl', 'rb') as f:
            model_data = pickle.load(f)
        logger.info(f"Model loaded successfully! Accuracy: {model_data['accuracy']:.4f}")
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise RuntimeError(f"Could not load model: {str(e)}")


def preprocess_features(features: CustomerFeatures) -> np.ndarray:
    """Preprocess customer features for prediction."""
    # Get encoders from loaded model
    encoders = model_data['encoders']

    # Create feature array in the correct order
    feature_values = []

    # Age (numerical)
    feature_values.append(features.age)

    # Gender (encoded)
    gender_encoded = encoders['gender'].transform([features.gender])[0]
    feature_values.append(gender_encoded)

    # Tenure (numerical)
    feature_values.append(features.tenure)

    # Usage Frequency (numerical)
    feature_values.append(features.usage_frequency)

    # Support Calls (numerical)
    feature_values.append(features.support_calls)

    # Payment Delay (numerical)
    feature_values.append(features.payment_delay)

    # Subscription Type (encoded)
    subscription_encoded = encoders['subscription'].transform([features.subscription_type])[0]
    feature_values.append(subscription_encoded)

    # Contract Length (ordinal encoded)
    contract_encoded = encoders['contract'][features.contract_length]
    feature_values.append(contract_encoded)

    # Total Spend (numerical)
    feature_values.append(features.total_spend)

    # Last Interaction (encoded)
    interaction_encoded = encoders['interaction'].transform([features.last_interaction])[0]
    feature_values.append(interaction_encoded)

    return np.array(feature_values).reshape(1, -1)


def get_risk_level(probability: float) -> str:
    """Determine risk level based on churn probability."""
    if probability < 0.3:
        return "Low"
    elif probability < 0.7:
        return "Medium"
    else:
        return "High"


@app.get("/health")
async def health_check():
    """Health check endpoint to verify API is running."""
    return {"status": "ok", "model_loaded": model_data is not None}


@app.post("/predict", response_model=PredictionResponse)
async def predict_churn(features: CustomerFeatures):
    """Predict customer churn probability."""
    if model_data is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    try:
        # Preprocess features
        processed_features = preprocess_features(features)

        # Make prediction
        model = model_data['model']
        prediction = model.predict(processed_features)[0]
        probability = model.predict_proba(processed_features)[0][1]  # Probability of churn (class 1)

        # Determine risk level
        risk_level = get_risk_level(probability)

        return PredictionResponse(
            churn_probability=round(probability, 4),
            churn_prediction=int(prediction),
            risk_level=risk_level
        )

    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Prediction failed: {str(e)}")