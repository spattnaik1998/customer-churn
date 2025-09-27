"""
Customer Churn Prediction Model Training Script

This script loads the customer churn datasets, preprocesses the data,
trains a Logistic Regression model, and saves it for deployment.
"""

import pandas as pd
import numpy as np
import pickle
import os
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


def load_data():
    """Load training and testing datasets."""
    print("Loading datasets...")

    # Load datasets (paths relative to project root)
    train_df = pd.read_csv('../data/customer_churn_dataset-training-master.csv')
    test_df = pd.read_csv('../data/customer_churn_dataset-testing-master.csv')

    print(f"Training dataset shape: {train_df.shape}")
    print(f"Testing dataset shape: {test_df.shape}")

    return train_df, test_df


def preprocess_data(train_df, test_df):
    """Preprocess the data by handling missing values and encoding categorical variables."""
    print("\nPreprocessing data...")

    # Create copies for processing
    train_processed = train_df.copy()
    test_processed = test_df.copy()

    # Remove rows with NULL values
    train_processed = train_processed.dropna()
    test_processed = test_processed.dropna()

    print(f"After removing NULL values:")
    print(f"Training dataset shape: {train_processed.shape}")
    print(f"Testing dataset shape: {test_processed.shape}")

    # Encode categorical variables
    print("\nEncoding categorical variables...")

    # Gender encoding
    le_gender = LabelEncoder()
    train_processed['Gender'] = le_gender.fit_transform(train_processed['Gender'])
    test_processed['Gender'] = le_gender.transform(test_processed['Gender'])

    # Subscription Type encoding
    le_subscription = LabelEncoder()
    train_processed['Subscription Type'] = le_subscription.fit_transform(train_processed['Subscription Type'])
    test_processed['Subscription Type'] = le_subscription.transform(test_processed['Subscription Type'])

    # Last Interaction encoding
    le_interaction = LabelEncoder()
    train_processed['Last Interaction'] = le_interaction.fit_transform(train_processed['Last Interaction'])
    test_processed['Last Interaction'] = le_interaction.transform(test_processed['Last Interaction'])

    # Contract Length ordinal encoding
    contract_mapping = {'Monthly': 0, 'Quarterly': 1, 'Annual': 2}
    train_processed['Contract Length'] = train_processed['Contract Length'].map(contract_mapping)
    test_processed['Contract Length'] = test_processed['Contract Length'].map(contract_mapping)

    # Target variable encoding
    le_churn = LabelEncoder()
    train_processed['Churn'] = le_churn.fit_transform(train_processed['Churn'])
    test_processed['Churn'] = le_churn.transform(test_processed['Churn'])

    # Store encoders for later use
    encoders = {
        'gender': le_gender,
        'subscription': le_subscription,
        'interaction': le_interaction,
        'contract': contract_mapping,
        'churn': le_churn
    }

    print("Encoding mappings:")
    print(f"Gender: {dict(zip(le_gender.classes_, le_gender.transform(le_gender.classes_)))}")
    print(f"Subscription Type: {dict(zip(le_subscription.classes_, le_subscription.transform(le_subscription.classes_)))}")
    print(f"Contract Length: {contract_mapping}")

    return train_processed, test_processed, encoders


def prepare_features(train_processed, test_processed):
    """Prepare feature matrices and target vectors."""
    print("\nPreparing features...")

    # Separate features and target
    X_train = train_processed.drop(['CustomerID', 'Churn'], axis=1)
    y_train = train_processed['Churn']

    X_test = test_processed.drop(['CustomerID', 'Churn'], axis=1)
    y_test = test_processed['Churn']

    print("Feature columns:")
    print(X_train.columns.tolist())
    print(f"\nTraining features shape: {X_train.shape}")
    print(f"Training target shape: {y_train.shape}")
    print(f"Test features shape: {X_test.shape}")
    print(f"Test target shape: {y_test.shape}")

    return X_train, X_test, y_train, y_test


def train_model(X_train, y_train):
    """Train the Logistic Regression model."""
    print("\nTraining Logistic Regression model...")

    # Initialize and train the model
    model = LogisticRegression(random_state=42, max_iter=1000)
    model.fit(X_train, y_train)

    print("Model training completed!")
    print(f"Model coefficients: {model.coef_[0]}")
    print(f"Model intercept: {model.intercept_[0]}")

    return model


def evaluate_model(model, X_test, y_test):
    """Evaluate the model on test data."""
    print("\nEvaluating model on test data...")

    # Make predictions
    y_pred = model.predict(X_test)

    # Calculate accuracy
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Test Accuracy: {accuracy:.4f}")

    # Detailed classification report
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    # Confusion matrix
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    return accuracy, y_pred


def save_model(model, encoders, accuracy):
    """Save the trained model and encoders."""
    print("\nSaving model and encoders...")

    # Create models directory if it doesn't exist (relative to project root)
    os.makedirs('../models', exist_ok=True)

    # Save the model
    model_data = {
        'model': model,
        'encoders': encoders,
        'accuracy': accuracy,
        'feature_columns': ['Age', 'Gender', 'Tenure', 'Usage Frequency', 'Support Calls',
                           'Payment Delay', 'Subscription Type', 'Contract Length',
                           'Total Spend', 'Last Interaction']
    }

    with open('../models/churn_model.pkl', 'wb') as f:
        pickle.dump(model_data, f)

    print("Model saved successfully as '../models/churn_model.pkl'")
    print(f"Model accuracy: {accuracy:.4f}")


def main():
    """Main training pipeline."""
    print("=== Customer Churn Prediction Model Training ===")

    # Load data
    train_df, test_df = load_data()

    # Preprocess data
    train_processed, test_processed, encoders = preprocess_data(train_df, test_df)

    # Prepare features
    X_train, X_test, y_train, y_test = prepare_features(train_processed, test_processed)

    # Train model
    model = train_model(X_train, y_train)

    # Evaluate model
    accuracy, y_pred = evaluate_model(model, X_test, y_test)

    # Save model
    save_model(model, encoders, accuracy)

    print("\n=== Training Pipeline Completed Successfully! ===")
    print(f"Final Model Accuracy: {accuracy:.4f}")


if __name__ == "__main__":
    main()