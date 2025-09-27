#!/bin/bash

# Build script for Streamlit frontend deployment on Netlify

set -e

echo "🏗️  Building Streamlit frontend for deployment..."

# Install Python dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Create deployment directory
echo "📁 Creating deployment structure..."
mkdir -p dist

# Copy frontend application
cp app/frontend.py dist/
cp requirements.txt dist/

# Create index.html for Netlify
cat > dist/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Customer Churn Prediction</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container {
            text-align: center;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            backdrop-filter: blur(10px);
        }
        .spinner {
            border: 4px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top: 4px solid white;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔮 Customer Churn Prediction</h1>
        <div class="spinner"></div>
        <p>Loading application...</p>
        <p><small>Note: Streamlit apps require server-side deployment.<br>
        This app is best deployed on platforms like Streamlit Cloud, Heroku, or Railway.</small></p>
        <div style="margin-top: 2rem;">
            <a href="https://churn-prediction-api.onrender.com/docs"
               style="color: white; text-decoration: none; background: rgba(255,255,255,0.2); padding: 10px 20px; border-radius: 10px; display: inline-block;">
               🚀 View API Documentation
            </a>
        </div>
    </div>
</body>
</html>
EOF

# Create runtime.txt for Python version
echo "python-3.11.0" > dist/runtime.txt

# Create Procfile for deployment platforms
echo "web: streamlit run frontend.py --server.port=\$PORT --server.address=0.0.0.0 --server.headless=true" > dist/Procfile

echo "✅ Frontend build complete!"
echo "📁 Files created in dist/ directory:"
ls -la dist/