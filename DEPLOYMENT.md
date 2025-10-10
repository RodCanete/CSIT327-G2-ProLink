# ProLink Deployment Guide

## Render Deployment Instructions

### Prerequisites
1. Render account (free tier available)
2. GitHub repository with your ProLink code
3. Supabase project set up

### Step 1: Prepare Your Repository

Ensure your repository contains:
- `build.sh` (executable build script)
- `requirements.txt` (with all dependencies)
- `prolink/prolink/settings.py` (configured for production)
- `env.example` (template for environment variables)

### Step 2: Create Render Web Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select your repository and branch

### Step 3: Configure Service Settings

**Basic Settings:**
- **Name**: `prolink`
- **Environment**: `Python 3`
- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn --chdir prolink prolink.wsgi:application`
- **Instance Type**: Free

### Step 4: Set Environment Variables

In Render dashboard, add these environment variables:

**Required Variables:**
```
SECRET_KEY=your-generated-secret-key
DEBUG=False
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
DATABASE_URL=your-supabase-postgresql-url
PYTHON_VERSION=3.11
```

**How to get these values:**
1. **SECRET_KEY**: Generate using `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
2. **Supabase credentials**: From your Supabase project settings
3. **DATABASE_URL**: From Supabase → Settings → Database → Connection string

### Step 5: Deploy

1. Click "Create Web Service"
2. Monitor the build logs
3. Wait for deployment to complete
4. Note your app URL (e.g., `https://prolink.onrender.com`)

### Step 6: Update Supabase Settings

1. Go to your Supabase dashboard
2. Navigate to Authentication → Settings
3. Update **Site URL** to your Render URL
4. Add your Render URL to **Redirect URLs**

### Step 7: Test Deployment

1. Visit your Render URL
2. Test user registration
3. Test user login
4. Verify static files (CSS/JS) load correctly

## Local Development

To run locally with production-like settings:

1. Copy `env.example` to `.env`
2. Fill in your actual values
3. Run: `python test_production_settings.py`

## Troubleshooting

### Common Issues:

**Build Fails:**
- Check build logs in Render dashboard
- Ensure `build.sh` is executable
- Verify all dependencies in `requirements.txt`

**Static Files Not Loading:**
- Check `STATIC_ROOT` and `STATICFILES_DIRS` in settings
- Ensure WhiteNoise is in middleware
- Run `collectstatic` locally to test

**Database Connection Issues:**
- Verify `DATABASE_URL` format
- Check Supabase connection settings
- Ensure database exists in Supabase

**Authentication Not Working:**
- Update Supabase redirect URLs
- Check environment variables are set correctly
- Verify Supabase keys are valid

## Free Tier Limitations

- App sleeps after 15 minutes of inactivity
- First request after sleep takes ~50 seconds
- 750 hours/month free
- Automatic deployments on git push

## Security Notes

- Never commit `.env` or `supabase_config.py` files
- Use different SECRET_KEY for production
- Enable HTTPS in production (automatic on Render)
- Regularly rotate API keys

## Support

If you encounter issues:
1. Check Render build/deploy logs
2. Test locally with production settings
3. Verify Supabase configuration
4. Check environment variables in Render dashboard

