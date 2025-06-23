# Railway Deployment Guide for Dynamic Pricing Engine

## 🚀 Quick Deploy

The Dynamic Pricing Engine is ready for Railway deployment! Follow these steps:

## Prerequisites

1. Railway account (sign up at https://railway.app)
2. Railway CLI installed (optional): `npm install -g @railway/cli`

## Deployment Steps

### 1. Deploy via Railway Dashboard

1. Go to https://railway.app/new
2. Select "Deploy from GitHub repo"
3. Connect your GitHub account and select `JPcasado88/dpe`
4. Railway will automatically detect the configuration

### 2. Set Environment Variables

In your Railway project dashboard, go to Variables and add:

```env
# Required Variables
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
PORT=8000

# Application Settings
APP_NAME=Dynamic Pricing Engine
APP_VERSION=1.0.0
DEBUG=False
LOG_LEVEL=INFO

# API Settings
API_PREFIX=/api/v1
CORS_ORIGINS=["*"]

# Pricing Constraints
MIN_MARGIN_PCT=15
MAX_PRICE_CHANGE_PCT=20
MIN_HOURS_BETWEEN_CHANGES=4

# Feature Flags
ENABLE_ML_OPTIMIZATION=true
ENABLE_AB_TESTING=true
ENABLE_COMPETITOR_TRACKING=true
ENABLE_ALERTS=true

# Security
SECRET_KEY=your-secret-key-here-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Add Required Services

In Railway dashboard, add these services to your project:

1. **PostgreSQL**
   - Click "New" → "Database" → "Add PostgreSQL"
   - Railway will automatically set DATABASE_URL

2. **Redis**
   - Click "New" → "Database" → "Add Redis"
   - Railway will automatically set REDIS_URL

### 4. Initialize Database

After deployment, run the database initialization:

```bash
# Using Railway CLI
railway run python scripts/init_db.py

# Or use the Railway dashboard's command palette
python scripts/init_db.py
```

### 5. Deploy Frontend Separately (Optional)

For the React frontend, create a separate Railway service:

1. Create new service in same project
2. Point to `frontend` directory
3. Set build command: `npm install && npm run build`
4. Set start command: `npm run serve`
5. Add environment variable: `REACT_APP_API_URL=https://your-backend-url.railway.app`

## 🔧 Configuration Details

### Backend Service

- **Build**: Automatically uses Nixpacks
- **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Health Check**: `GET /health`
- **Port**: Uses Railway's dynamic PORT variable

### Database

- PostgreSQL 15+ recommended
- Automatic connection pooling
- Schema auto-migrates on first run

### Redis

- Used for caching optimization results
- TTL configured per cache type
- Graceful fallback if unavailable

## 📊 Post-Deployment

### 1. Verify Deployment

Check these endpoints:

- Health: `https://your-app.railway.app/health`
- API Docs: `https://your-app.railway.app/docs`
- Metrics: `https://your-app.railway.app/metrics`

### 2. Load Sample Data

```bash
railway run python scripts/generate_data.py
```

### 3. Monitor Performance

- Check Railway metrics dashboard
- Set up alerts for errors
- Monitor database performance

## 🚨 Troubleshooting

### Database Connection Issues

If you see database connection errors:

1. Ensure PostgreSQL service is running
2. Check DATABASE_URL format (Railway provides postgres://, we need postgresql://)
3. The app automatically handles this conversion

### Redis Connection Issues

Redis is optional. The app will work without it but with reduced performance.

### Memory Issues

If you encounter memory issues:

1. Upgrade to a paid Railway plan
2. Or reduce ML model complexity in settings

## 🎯 Production Checklist

- [ ] Change SECRET_KEY to a secure value
- [ ] Set DEBUG=False
- [ ] Configure CORS_ORIGINS for your frontend domain
- [ ] Set up monitoring alerts
- [ ] Configure backup strategy for PostgreSQL
- [ ] Set up custom domain (optional)

## 💰 Estimated Costs

On Railway Hobby plan ($5/month):
- Backend: ~$5-10/month
- PostgreSQL: ~$5/month
- Redis: ~$5/month
- **Total: ~$15-20/month**

## 🔗 Useful Links

- Railway Docs: https://docs.railway.app
- API Documentation: `https://your-app.railway.app/docs`
- GitHub Repo: https://github.com/JPcasado88/dpe

## Support

For deployment issues:
1. Check Railway logs in dashboard
2. Verify all environment variables are set
3. Ensure database migrations ran successfully

Happy deploying! 🚀