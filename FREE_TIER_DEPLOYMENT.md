# 🆓 Free Tier Deployment Guide

Deploy the Dynamic Pricing Engine demo for **$0/month** on Railway's free tier!

## What's Included in Demo

✅ **Working Features:**
- ML-powered price optimization
- 3 demo products
- Real-time optimization API
- Impact projections
- API documentation

❌ **Limitations:**
- No database (uses in-memory storage)
- No Redis (uses in-memory cache)
- Data resets on restart
- Limited to demo products

## Quick Deploy (Under 2 Minutes!)

### Option 1: One-Click Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https%3A%2F%2Fgithub.com%2FJPcasado88%2Fdpe&envs=DEMO_MODE&DEMO_MODEDesc=Enables+lightweight+demo+mode&DEMO_MODEDefault=true)

### Option 2: Manual Deploy

1. **Fork the repo** (if you haven't already)
2. **Go to Railway**
   ```
   https://railway.app/new
   ```

3. **Deploy from GitHub**
   - Select your forked repo
   - Railway auto-detects the config

4. **Use Demo Configuration**
   - In Railway settings, change the start command to:
   ```
   cd backend && python demo_server.py
   ```

5. **That's it!** No environment variables needed for demo

## 🎯 Demo Endpoints

Once deployed, try these endpoints:

```bash
# Check health
curl https://your-app.railway.app/health

# View all products
curl https://your-app.railway.app/api/products

# Optimize a product price
curl -X POST https://your-app.railway.app/api/optimize/DEMO-001

# See total impact simulation
curl https://your-app.railway.app/api/demo/impact
```

## 📊 What You'll See

The demo shows:
- **+10-15% revenue increase** potential
- Price optimization for 3 product categories
- Real ML algorithms in action
- API response times < 100ms

## 💰 Cost Breakdown

**Railway Free Tier includes:**
- $5 free credits/month
- 500 MB RAM
- 1 GB disk
- Shared CPU

**Demo app uses:**
- ~100-200 MB RAM
- <50 MB disk
- Minimal CPU

**Result: Runs free indefinitely!** 🎉

## 🚀 Upgrade Path

When ready for production:

1. **Add PostgreSQL** ($5/month)
   ```bash
   railway add postgresql
   ```

2. **Add Redis** ($5/month)
   ```bash
   railway add redis
   ```

3. **Switch to Full Version**
   - Change start command back to: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Add environment variables
   - Run database migrations

## 📈 Demo vs Production

| Feature | Demo | Production |
|---------|------|------------|
| Products | 3 | Unlimited |
| Storage | Memory | PostgreSQL |
| Cache | Memory | Redis |
| Persistence | No | Yes |
| A/B Testing | No | Yes |
| Monitoring | Basic | Full |
| Cost | $0 | ~$15-20/mo |

## 🎮 Try It Now!

1. Deploy in 2 minutes
2. Test the API
3. See the ROI potential
4. Upgrade when ready

No credit card required! 🆓

## Example API Response

```json
{
  "demo_summary": {
    "products_analyzed": 3,
    "average_revenue_impact": "+12.3%",
    "projected_monthly_impact": "$12,300",
    "optimizations": [
      {
        "product": "Wireless Gaming Headset",
        "current_price": "$89.99",
        "optimal_price": "$84.99",
        "revenue_impact": "+8.5%"
      }
    ]
  }
}
```

## Need Help?

- 📚 [Full Documentation](/README.md)
- 🐛 [GitHub Issues](https://github.com/JPcasado88/dpe/issues)
- 📧 Contact: your-email@example.com

Start optimizing prices today - for free! 🚀