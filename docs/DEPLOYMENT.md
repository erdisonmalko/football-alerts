# Deployment Guide

This guide covers deploying the full-stack application to Railway.

## Overview

The application is deployed as three separate services on Railway:

1. **API** — FastAPI backend with Celery worker and beat scheduler
2. **Frontend** — React app served with Nginx
3. **Database** — PostgreSQL (Supabase)
4. **Cache** — Redis

## Prerequisites

- GitHub repository with code pushed
- Railway account (https://railway.app)
- Supabase account for managed PostgreSQL
- API keys for:
  - football-data.org
  - Resend (email service)
  - Google OAuth credentials

## Railway Setup

### 1. Create Railway Project

1. Log in to Railway: https://railway.app
2. Click "New Project"
3. Select "GitHub Repo" and authorize Railway
4. Select your football-alerts repository

### 2. Add Services

#### API Service

1. Click "Add Service" → "Docker"
2. Connect your repository
3. Configure:
   - **Root Directory**: `.` (project root)
   - **Dockerfile**: `Dockerfile` (for API)
   - **Start Command**: `uvicorn app.v1.main:app --host 0.0.0.0 --port 8000`

#### Frontend Service

1. Click "Add Service" → "Docker"
2. Connect repository
3. Configure:
   - **Root Directory**: `frontend/v1`
   - **Dockerfile**: `Dockerfile.prod`
   - **Start Command**: `nginx -g 'daemon off;'`
   - **Port**: 3000

#### Database (PostgreSQL)

1. Click "Add Service" → "PostgreSQL"
2. Railway generates DATABASE_URL automatically
3. Save the credentials

#### Cache (Redis)

1. Click "Add Service" → "Redis"
2. Railway generates REDIS_URL automatically

### 3. Environment Variables

Set in Railway dashboard for each service:

#### API Service

```env
# App
APP_ENV=production
SECRET_KEY=<generate-secure-random-key>
ADMIN_KEY=<generate-secure-random-key>

# Database
DATABASE_URL=${{Postgres.DATABASE_URL}}
DATABASE_URL_SYNC=${{Postgres.DATABASE_PUBLIC_URL}}
DATABASE_USER=${{Postgres.DATABASE_USER}}
DATABASE_PASSWORD=${{Postgres.DATABASE_PASSWORD}}

# Redis
REDIS_URL=${{Redis.REDIS_URL}}

# API Keys
FOOTBALL_DATA_API_KEY=<your-key>
RESEND_API_KEY=<your-key>
EMAIL_FROM=alerts@football.app
EMAIL_FROM_NAME=Football Alerts

# Frontend
FRONTEND_URL=https://your-frontend-domain.railway.app

# Google OAuth
GOOGLE_CLIENT_ID=<your-id>
GOOGLE_CLIENT_SECRET=<your-secret>
GOOGLE_REDIRECT_URI=https://your-api-domain.railway.app/api/v1/auth/google/callback
```

#### Frontend Service

```env
VITE_API_URL=https://your-api-domain.railway.app/api/v1
VITE_FRONTEND_URL=https://your-frontend-domain.railway.app
```

### 4. Run Database Migrations

After deploying API service:

```bash
# Via Railway CLI
railway run alembic upgrade head

# Or via Dashboard
# - Go to API service
# - Click "Deploy" → "View Logs"
# - Run command manually
```

### 5. Configure Domain Names

1. In Railway dashboard, go to each service
2. Click "Settings"
3. Under "Networking", generate or add custom domain
4. Update Google OAuth redirect URI if using custom domain

## Docker Configuration

### API Dockerfile

The root `Dockerfile` builds the FastAPI API:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Migrations run on container start
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.v1.main:app --host 0.0.0.0"]
```

### Frontend Dockerfile

`frontend/v1/Dockerfile.prod` builds and serves the React app:

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine

COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Environment-Specific Configuration

### Production Settings

```env
APP_ENV=production
DEBUG=false
LOG_LEVEL=info
```

### Staging Settings

```env
APP_ENV=staging
DEBUG=false
LOG_LEVEL=debug
```

### Database Backups

Supabase automatically backs up PostgreSQL:

- **Backup Frequency**: Daily
- **Retention**: 30 days
- **Restore**: Via Supabase dashboard

To restore from backup:

1. Go to Supabase project dashboard
2. Click "Backups"
3. Select backup date
4. Click "Restore"

## Health Checks

Railway automatically configures health checks for services:

- **API**: `GET /docs` returns 200 OK
- **Frontend**: `GET /` returns 200 OK
- **Database**: PostgreSQL connection test
- **Redis**: Redis ping

If health checks fail, the service restarts automatically.

## Scaling

### API Service

To handle more concurrent users:

1. In Railway dashboard, go to API service
2. Click "Settings"
3. Adjust under "Compute":
   - **Instances**: Number of replicas (auto-scale)
   - **CPU**: vCPU allocation
   - **Memory**: RAM allocation

### Database

To upgrade PostgreSQL resources:

1. In Supabase dashboard
2. Go to "Settings" → "Billing"
3. Upgrade plan or add more resources

### Frontend

Frontend is typically lightweight; rarely needs scaling.

## Monitoring

### Logs

View service logs in Railway dashboard:

1. Click service
2. Click "Logs" tab
3. Real-time log stream with filtering

### Metrics

Monitor service health:

- CPU usage
- Memory usage
- Network I/O
- Request latency
- Error rates

Available under each service's "Monitoring" tab.

### Alerts

Set up alerts for critical events:

1. Go to project settings
2. Click "Alerts"
3. Configure thresholds for:
   - High CPU usage
   - Low memory
   - Service crashes
   - High error rate

## CI/CD Pipeline

Railway automatically:

1. Watches GitHub repository for pushes
2. Builds Docker images
3. Runs migrations (if configured)
4. Deploys to running services
5. Performs health checks

### Manual Deployments

To trigger deployment without code push:

```bash
# Via Railway CLI
railway deploy

# Or via Dashboard
# - Click service
# - Click "Deploy" 
# - Select source (latest code)
# - Click "Deploy Now"
```

## Rollback

To rollback to previous deployment:

1. In Railway dashboard, click service
2. Click "Deployments" tab
3. Select previous deployment
4. Click "Redeploy"

This rebuilds from the same source and redeploys.

## Security

### API Keys in Production

- Never commit API keys to Git
- Store in Railway environment variables (encrypted)
- Use separate keys for staging/production
- Rotate keys quarterly

### Database Security

- PostgreSQL password: Auto-generated by Supabase
- Connection string includes credentials: **Keep SECRET_KEY and DATABASE_URL confidential**
- All connections encrypted via TLS/SSL
- Restrict database access to API service only

### Frontend Secrets

- No secrets should be in frontend code
- `VITE_` prefixed variables are exposed in bundle (use only for public config)
- Keep API keys and credentials on backend only

## Troubleshooting

### Service won't start

1. Check logs: `railway logs`
2. Verify environment variables are set
3. Check Dockerfile syntax
4. Ensure entrypoint script exists and is executable

### Database connection failed

```bash
# Test connection
railway run psql $DATABASE_URL -c "SELECT 1"

# Check if migrations are applied
railway run alembic current
```

### High memory usage

1. Review logs for memory leaks
2. Check number of open connections
3. Increase memory allocation
4. Optimize queries in database

### Frontend not loading

1. Check nginx configuration
2. Verify API URL is correct (must be accessible from frontend)
3. Check CORS settings in API
4. Review browser console for errors

### Celery tasks not running

1. Verify Redis connection
2. Check Celery worker is running: `railway logs celery-worker`
3. Verify beat scheduler is running: `railway logs celery-beat`
4. Check task is registered in celery_app

## Backup and Recovery

### Database Backup

```bash
# Manual backup
railway run pg_dump $DATABASE_URL > backup.sql

# Restore
railway run psql $DATABASE_URL < backup.sql
```

### Code Repository

Always maintain Git history:

```bash
git push origin main  # Pushes to GitHub
# Railway automatically watches and redeploys
```

## Performance Optimization

### Database

- Add indexes on frequently queried columns
- Use connection pooling (Railway provides)
- Monitor slow queries in logs

### Frontend

- Build optimization: Vite minifies and code-splits
- Enable gzip compression in nginx.conf
- Cache static assets with long TTL

### API

- Use async/await for I/O operations
- Implement pagination for large datasets
- Cache responses where appropriate
- Use database indexes

## Production Checklist

Before deploying to production:

- [ ] All environment variables set and verified
- [ ] Database backups configured
- [ ] SSL/TLS certificates configured
- [ ] Domain names pointing to correct services
- [ ] Health checks passing
- [ ] Logs being monitored
- [ ] Error tracking configured
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] Admin endpoints protected
- [ ] Database migrations applied
- [ ] Initial data seed (if needed) completed

## Support

- Railway Docs: https://docs.railway.app
- FastAPI Docs: https://fastapi.tiangolo.com
- React Docs: https://react.dev
- PostgreSQL Docs: https://www.postgresql.org/docs
