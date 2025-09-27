"""
Customer Churn Prediction Frontend

Streamlit application for interacting with the churn prediction API.
"""

import streamlit as st
import requests
import pandas as pd
import json
from typing import Dict, Any
import io

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"

def check_api_health() -> bool:
    """Check if the FastAPI backend is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def predict_single_customer(customer_data: Dict[str, Any]) -> Dict[str, Any]:
    """Send single customer prediction request to API."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/predict",
            json=customer_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"API Error: {response.status_code} - {response.text}"}

    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Connection Error: {str(e)}"}

def predict_batch_customers(csv_file) -> Dict[str, Any]:
    """Send batch prediction request to API."""
    try:
        files = {"file": ("batch_data.csv", csv_file, "text/csv")}
        response = requests.post(
            f"{API_BASE_URL}/predict-batch",
            files=files,
            timeout=60
        )

        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"API Error: {response.status_code} - {response.text}"}

    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Connection Error: {str(e)}"}

def display_prediction_result(result: Dict[str, Any]):
    """Display single prediction result."""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Churn Probability", f"{result['churn_probability']:.2%}")

    with col2:
        prediction_text = "Will Churn" if result['churn_prediction'] == 1 else "Will Stay"
        st.metric("Prediction", prediction_text)

    with col3:
        risk_color = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}
        st.metric("Risk Level", f"{risk_color.get(result['risk_level'], '⚪')} {result['risk_level']}")

def display_batch_results(batch_result: Dict[str, Any]):
    """Display batch prediction results."""
    data = batch_result['data']

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Predictions", data['total_predictions'])
    with col2:
        st.metric("Successful", data['successful_predictions'])
    with col3:
        st.metric("Failed", data['failed_predictions'])

    # Results table
    if data['results']:
        results_df = pd.DataFrame([
            {
                "Row": r['row_index'],
                "Customer ID": r['customer_id'] or 'N/A',
                "Churn Probability": f"{r['churn_probability']:.2%}",
                "Prediction": "Will Churn" if r['churn_prediction'] == 1 else "Will Stay",
                "Risk Level": r['risk_level'],
                "Error": r['error'] or 'None'
            }
            for r in data['results']
        ])

        st.dataframe(results_df, use_container_width=True)

        # Download results as CSV
        csv_buffer = io.StringIO()
        results_df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="Download Results as CSV",
            data=csv_buffer.getvalue(),
            file_name="churn_predictions.csv",
            mime="text/csv"
        )

def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Customer Churn Prediction",
        page_icon="📊",
        layout="wide"
    )

    # Header
    st.title("🔮 Customer Churn Prediction")
    st.markdown("Predict customer churn using machine learning")

    # Check API health
    if not check_api_health():
        st.error("❌ Cannot connect to the prediction API. Please ensure the FastAPI backend is running on http://127.0.0.1:8000")
        st.info("Run: `cd app && uvicorn main:app --reload`")
        return

    st.success("✅ Connected to prediction API")

    # Tabs for different prediction modes
    tab1, tab2 = st.tabs(["🎯 Single Prediction", "📊 Batch Predictions"])

    with tab1:
        st.header("Single Customer Prediction")

        # Create form for single prediction
        with st.form("single_prediction_form"):
            col1, col2 = st.columns(2)

            with col1:
                age = st.number_input("Age", min_value=18, max_value=100, value=35)
                gender = st.selectbox("Gender", ["Male", "Female"])
                tenure = st.number_input("Tenure (months)", min_value=0, max_value=100, value=24)
                usage_frequency = st.number_input("Usage Frequency", min_value=0, max_value=50, value=15)
                support_calls = st.number_input("Support Calls", min_value=0, max_value=20, value=3)

            with col2:
                payment_delay = st.number_input("Payment Delay (days)", min_value=0, max_value=60, value=10)
                subscription_type = st.selectbox("Subscription Type", ["Basic", "Standard", "Premium"])
                contract_length = st.selectbox("Contract Length", ["Monthly", "Quarterly", "Annual"])
                total_spend = st.number_input("Total Spend ($)", min_value=0, max_value=5000, value=750)
                last_interaction = st.number_input("Last Interaction (days ago)", min_value=1, max_value=30, value=15)

            submitted = st.form_submit_button("🔮 Predict Churn", use_container_width=True)

            if submitted:
                # Prepare data for API
                customer_data = {
                    "age": age,
                    "gender": gender,
                    "tenure": tenure,
                    "usage_frequency": usage_frequency,
                    "support_calls": support_calls,
                    "payment_delay": payment_delay,
                    "subscription_type": subscription_type,
                    "contract_length": contract_length,
                    "total_spend": total_spend,
                    "last_interaction": last_interaction
                }

                # Make prediction
                with st.spinner("Making prediction..."):
                    result = predict_single_customer(customer_data)

                if result["success"]:
                    st.success("Prediction completed!")
                    display_prediction_result(result["data"])
                else:
                    st.error(f"Prediction failed: {result['error']}")

    with tab2:
        st.header("Batch Customer Predictions")

        st.markdown("""
        Upload a CSV file with customer data to get predictions for multiple customers.

        **Required columns:**
        - Age, Gender, Tenure, Usage Frequency, Support Calls
        - Payment Delay, Subscription Type, Contract Length
        - Total Spend, Last Interaction
        - CustomerID (optional)
        """)

        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type="csv",
            help="Upload a CSV file with customer data for batch predictions"
        )

        if uploaded_file is not None:
            # Preview the uploaded file
            try:
                df_preview = pd.read_csv(uploaded_file)
                st.subheader("📋 File Preview")
                st.dataframe(df_preview.head(), use_container_width=True)
                st.info(f"File contains {len(df_preview)} rows")

                # Reset file pointer for API call
                uploaded_file.seek(0)

                # Predict button
                if st.button("🚀 Run Batch Predictions", use_container_width=True):
                    with st.spinner("Processing batch predictions..."):
                        result = predict_batch_customers(uploaded_file)

                    if result["success"]:
                        st.success("Batch predictions completed!")
                        display_batch_results(result)
                    else:
                        st.error(f"Batch prediction failed: {result['error']}")

            except Exception as e:
                st.error(f"Error reading CSV file: {str(e)}")
        else:
            # Show sample data format
            st.subheader("📝 Sample Data Format")
            sample_data = {
                "CustomerID": [1001, 1002, 1003],
                "Age": [35, 45, 28],
                "Gender": ["Male", "Female", "Male"],
                "Tenure": [24, 12, 36],
                "Usage Frequency": [15, 8, 22],
                "Support Calls": [3, 7, 1],
                "Payment Delay": [10, 25, 5],
                "Subscription Type": ["Standard", "Basic", "Premium"],
                "Contract Length": ["Annual", "Monthly", "Annual"],
                "Total Spend": [750, 320, 1200],
                "Last Interaction": [15, 5, 20]
            }

            sample_df = pd.DataFrame(sample_data)
            st.dataframe(sample_df, use_container_width=True)

            # Download sample file
            csv_buffer = io.StringIO()
            sample_df.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 Download Sample CSV",
                data=csv_buffer.getvalue(),
                file_name="sample_customers.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()