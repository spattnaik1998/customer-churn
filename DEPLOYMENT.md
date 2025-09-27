# Deployment Guide

This guide explains how to deploy the Customer Churn Prediction application using GitHub Actions, Render, and Netlify.

## 🚀 Overview

- **Backend API**: Deployed to Render using Docker
- **Frontend**: Deployed to Streamlit Cloud or Railway (recommended for Streamlit apps)
- **CI/CD**: GitHub Actions for automated deployment

## 📋 Prerequisites

### GitHub Repository Setup
1. Push your code to GitHub
2. Enable GitHub Actions in repository settings

### Required Secrets

Add these secrets to your GitHub repository (`Settings > Secrets and variables > Actions`):

#### For Render Deployment
```
RENDER_API_KEY=your_render_api_key
RENDER_SERVICE_ID=your_render_service_id
```

#### For Netlify Deployment (Alternative)
```
NETLIFY_AUTH_TOKEN=your_netlify_auth_token
NETLIFY_SITE_ID=your_netlify_site_id
```

## 🐳 Backend Deployment (Render)

### Option 1: Using GitHub Actions (Recommended)
1. Get your Render API key from [Render Dashboard](https://dashboard.render.com/account/settings)
2. Create a new Web Service on Render connected to your GitHub repo
3. Copy the Service ID from the URL
4. Add secrets to GitHub repository
5. Push to main branch to trigger deployment

### Option 2: Manual Render Deployment
1. Connect your GitHub repository to Render
2. Use these settings:
   ```
   Build Command: pip install pandas numpy scikit-learn && cd src && python train_model.py && cd ..
   Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
   Dockerfile Path: ./app/Dockerfile.backend
   Docker Context: .
   ```

### Environment Variables on Render
```
PYTHONPATH=/app
PORT=8000
HOST=0.0.0.0
```

## 🌐 Frontend Deployment

### Option 1: Streamlit Cloud (Recommended)
1. Go to [Streamlit Cloud](https://share.streamlit.io/)
2. Connect your GitHub repository
3. Deploy from `app/frontend.py`
4. Set environment variable:
   ```
   API_BASE_URL=https://your-render-app.onrender.com
   ```

### Option 2: Railway
1. Go to [Railway](https://railway.app/)
2. Connect your GitHub repository
3. Deploy with these settings:
   ```
   Start Command: streamlit run app/frontend.py --server.port $PORT --server.address 0.0.0.0
   ```
4. Set environment variable:
   ```
   API_BASE_URL=https://your-render-app.onrender.com
   ```

### Option 3: Heroku
1. Create a new Heroku app
2. Set buildpacks:
   ```bash
   heroku buildpacks:set heroku/python
   ```
3. Deploy using Git:
   ```bash
   git subtree push --prefix=app heroku main
   ```

## 🔧 Environment Configuration

### Backend (Render) Environment Variables
```bash
# Required
PYTHONPATH=/app
PORT=8000
HOST=0.0.0.0

# Optional
LOG_LEVEL=INFO
MODEL_PATH=/app/models/churn_model.pkl
```

### Frontend Environment Variables
```bash
# Required - Update with your actual Render URL
API_BASE_URL=https://your-app-name.onrender.com

# Optional
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

## 📊 Monitoring and Health Checks

### Health Check Endpoints
- **Backend**: `https://your-app.onrender.com/health`
- **API Docs**: `https://your-app.onrender.com/docs`

### Monitoring
- Render provides built-in monitoring and logs
- GitHub Actions provides deployment status
- Streamlit Cloud shows app status and logs

## 🔄 CI/CD Pipeline

The GitHub Actions workflow automatically:

1. **Tests**: Runs tests on every push/PR
2. **Builds**: Creates Docker images
3. **Deploys**: Updates services on Render
4. **Notifies**: Provides deployment status

### Workflow Triggers
- Push to `main` branch: Full deployment
- Pull requests: Testing only
- Manual triggers: Available in Actions tab

## 🐛 Troubleshooting

### Common Issues

1. **Model Not Found**
   - Ensure the training script runs successfully
   - Check that `models/churn_model.pkl` exists
   - Verify volume mounts in Docker

2. **API Connection Failed**
   - Check `API_BASE_URL` environment variable
   - Ensure backend is deployed and healthy
   - Verify CORS settings if needed

3. **Build Failures**
   - Check requirements.txt for missing dependencies
   - Verify Dockerfile paths are correct
   - Ensure secrets are properly configured

### Logs Access
- **Render**: Dashboard > Service > Logs
- **GitHub Actions**: Repository > Actions > Workflow run
- **Streamlit Cloud**: App dashboard > Logs

## 🚀 Quick Start Commands

### Deploy Backend to Render
```bash
# Automatic via GitHub Actions
git push origin main

# Manual using Render CLI
render services create --name churn-api --dockerfile ./app/Dockerfile.backend
```

### Deploy Frontend to Streamlit Cloud
1. Visit [share.streamlit.io](https://share.streamlit.io/)
2. Authenticate with GitHub
3. Select repository and `app/frontend.py`
4. Add API_BASE_URL environment variable

## 📱 Alternative Deployment Options

### Docker Compose (Local/VPS)
```bash
docker-compose up -d
```

### Kubernetes
```bash
# Generate K8s manifests from docker-compose
kompose convert
kubectl apply -f .
```

### AWS/GCP/Azure
Use the Docker images built by GitHub Actions:
- `ghcr.io/your-username/your-repo/backend:latest`
- `ghcr.io/your-username/your-repo/frontend:latest`

---

## 🔗 Useful Links

- [Render Documentation](https://render.com/docs)
- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-cloud)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)

## 📞 Support

For deployment issues:
1. Check the troubleshooting section above
2. Review logs in the respective platforms
3. Verify environment variables and secrets
4. Test locally with Docker first