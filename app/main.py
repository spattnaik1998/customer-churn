"""
Customer Churn Prediction API

FastAPI application for serving churn prediction model.
"""

import pickle
import numpy as np
import pandas as pd
import io
from typing import Optional, List
from fastapi import FastAPI, HTTPException, UploadFile, File
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


class BatchPredictionItem(BaseModel):
    """Pydantic model for individual batch prediction result."""
    row_index: int
    customer_id: Optional[str] = None
    churn_probability: float
    churn_prediction: int
    risk_level: str
    error: Optional[str] = None


class BatchPredictionResponse(BaseModel):
    """Pydantic model for batch prediction response."""
    total_predictions: int
    successful_predictions: int
    failed_predictions: int
    results: List[BatchPredictionItem]


@app.on_event("startup")
async def load_model():
    """Load the trained model at startup."""
    global model_data
    try:
        logger.info("Loading churn prediction model...")
        # Try different model paths for flexibility
        model_paths = ['../models/churn_model.pkl', 'models/churn_model.pkl', './models/churn_model.pkl']

        for model_path in model_paths:
            try:
                with open(model_path, 'rb') as f:
                    model_data = pickle.load(f)
                logger.info(f"Model loaded successfully from {model_path}! Accuracy: {model_data['accuracy']:.4f}")
                break
            except FileNotFoundError:
                continue

        if model_data is None:
            raise FileNotFoundError("Model file not found in any expected location")

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


def preprocess_batch_features(df: pd.DataFrame) -> np.ndarray:
    """Preprocess a batch of customer features for prediction."""
    encoders = model_data['encoders']

    # Create a copy to avoid modifying original dataframe
    processed_df = df.copy()

    # Apply encodings to each column
    processed_df['Gender'] = encoders['gender'].transform(processed_df['Gender'])
    processed_df['Subscription Type'] = encoders['subscription'].transform(processed_df['Subscription Type'])
    processed_df['Last Interaction'] = encoders['interaction'].transform(processed_df['Last Interaction'])

    # Contract Length ordinal encoding
    contract_mapping = encoders['contract']
    processed_df['Contract Length'] = processed_df['Contract Length'].map(contract_mapping)

    # Select features in the correct order
    feature_columns = ['Age', 'Gender', 'Tenure', 'Usage Frequency', 'Support Calls',
                      'Payment Delay', 'Subscription Type', 'Contract Length',
                      'Total Spend', 'Last Interaction']

    return processed_df[feature_columns].values


def validate_csv_columns(df: pd.DataFrame) -> bool:
    """Validate that CSV has required columns."""
    required_columns = [
        'Age', 'Gender', 'Tenure', 'Usage Frequency', 'Support Calls',
        'Payment Delay', 'Subscription Type', 'Contract Length',
        'Total Spend', 'Last Interaction'
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    return True


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


@app.post("/predict-batch", response_model=BatchPredictionResponse)
async def predict_batch_churn(file: UploadFile = File(...)):
    """Predict churn for multiple customers from CSV file."""
    if model_data is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV file")

    try:
        # Read CSV file
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))

        logger.info(f"Processing batch prediction for {len(df)} rows")

        # Validate required columns
        validate_csv_columns(df)

        results = []
        successful_predictions = 0
        failed_predictions = 0

        # Process each row
        for index, row in df.iterrows():
            try:
                # Create individual dataframe for this row
                row_df = pd.DataFrame([row])

                # Get customer ID if available
                customer_id = row.get('CustomerID', row.get('Customer_ID', None))
                if customer_id is not None:
                    customer_id = str(customer_id)

                # Preprocess features
                processed_features = preprocess_batch_features(row_df)

                # Make prediction
                model = model_data['model']
                prediction = model.predict(processed_features)[0]
                probability = model.predict_proba(processed_features)[0][1]

                # Determine risk level
                risk_level = get_risk_level(probability)

                # Add successful result
                results.append(BatchPredictionItem(
                    row_index=index,
                    customer_id=customer_id,
                    churn_probability=round(probability, 4),
                    churn_prediction=int(prediction),
                    risk_level=risk_level
                ))

                successful_predictions += 1

            except Exception as row_error:
                # Add failed result
                logger.warning(f"Failed to process row {index}: {str(row_error)}")
                results.append(BatchPredictionItem(
                    row_index=index,
                    customer_id=str(row.get('CustomerID', row.get('Customer_ID', 'Unknown'))),
                    churn_probability=0.0,
                    churn_prediction=0,
                    risk_level="Unknown",
                    error=str(row_error)
                ))

                failed_predictions += 1

        logger.info(f"Batch prediction completed: {successful_predictions} successful, {failed_predictions} failed")

        return BatchPredictionResponse(
            total_predictions=len(df),
            successful_predictions=successful_predictions,
            failed_predictions=failed_predictions,
            results=results
        )

    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Batch prediction failed: {str(e)}")