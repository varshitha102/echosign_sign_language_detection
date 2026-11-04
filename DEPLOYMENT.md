# Deployment Guide - EchoSign

This guide explains how to deploy EchoSign to both Vercel and Render.

---

## 🔧 Code Updates Made (2026)

The following production-ready changes have been applied to modernize the codebase:

### 1. Fixed `app.py`
- ✅ Changed hardcoded `SECRET_KEY` to use environment variable
- ✅ Removed `debug=True` in production - now uses `FLASK_DEBUG` env var
- ✅ Added `host='0.0.0.0'` for cloud deployment compatibility
- ✅ Added dynamic PORT from environment variable

### 2. Updated `requirements.txt`
- ✅ Added `gunicorn>=21.2.0` for production WSGI server

### 3. Added New Configuration Files
- ✅ `pyproject.toml` - Python project metadata for Vercel
- ✅ `vercel.json` - Vercel routing and CORS configuration
- ✅ `.vercelignore` - Exclude unnecessary files from Vercel deployment
- ✅ `Procfile` - Render deployment configuration
- ✅ `.env.example` - Environment variable template
- ✅ Updated `.gitignore` - Comprehensive ignore patterns

---

## 🚀 Deploy to Vercel

### Prerequisites
- Vercel account (free at vercel.com)
- GitHub/GitLab/Bitbucket account

### Method 1: Vercel CLI (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy from project directory
cd echosign_sign_language_detection
vercel

# Follow the prompts:
# - Link to existing project? No
# - Project name: echosign
# - Directory: ./
# - Settings: Use defaults (auto-detected Flask)
```

### Method 2: Vercel Dashboard

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your Git repository
3. **Framework Preset**: Flask (auto-detected)
4. **Root Directory**: `./`
5. **Build Command**: Leave empty (Vercel auto-detects)
6. **Output Directory**: Leave empty
7. Click **Deploy**

### Environment Variables (Vercel)

In Vercel Dashboard → Settings → Environment Variables:

```
SECRET_KEY=<generate-a-secure-random-key>
FLASK_DEBUG=false
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Vercel-Specific Notes

- ✅ **Zero-configuration deployment** - Vercel automatically detects Flask
- ✅ **Serverless Functions** - Your app runs as Vercel Functions with auto-scaling
- ✅ **Preview deployments** - Every git branch gets a preview URL
- ⚠️ **Model files**: Large model files (`.keras`, `.tflite`) may hit Vercel's size limits. Consider:
  - Hosting models on cloud storage (AWS S3, Cloudflare R2)
  - Using model quantization to reduce size
  - Only deploying with `.tflite` for ESP32 compatibility

---

## 🚀 Deploy to Render

### Prerequisites
- Render account (free at render.com)
- GitHub/GitLab/Bitbucket account

### Method 1: Render Dashboard

1. Go to [render.com/new](https://render.com/new)
2. Click **New +** → **Web Service**
3. Connect your Git repository
4. **Name**: echosign
5. **Region**: Choose closest to your users
6. **Branch**: main
7. **Runtime**: Python 3
8. **Build Command**: `pip install -r requirements.txt`
9. **Start Command**: `gunicorn app:app --workers 1 --threads 8 --timeout 120 --bind 0.0.0.0:$PORT`
10. **Instance Type**: Free (or paid for better performance)
11. Click **Create Web Service**

### Environment Variables (Render)

In Render Dashboard → Web Service → Environment:

```
SECRET_KEY=<generate-a-secure-random-key>
FLASK_DEBUG=false
PORT=5000
```

### Render-Specific Notes

- ✅ **Native Python support** - Render is optimized for Flask/Python
- ✅ **Persistent storage** - Better for model files than Vercel
- ✅ **Free tier available** - Limited but usable for testing
- ✅ **Simple configuration** - Just a Procfile and requirements.txt
- ⚠️ **Free tier spins down** - Service sleeps after 15 min inactivity

---

## 🧪 Local Testing Before Deployment

### Test the production configuration locally:

```bash
# Activate virtual environment
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
set SECRET_KEY=test-secret-key-for-local
set FLASK_DEBUG=false
set PORT=5000

# Run with gunicorn (simulates production)
gunicorn app:app --workers 1 --threads 8 --timeout 120 --bind 0.0.0.0:5000

# Or run with Flask (for development)
python app.py
```

### Test API endpoints:

```bash
# Health check
curl http://localhost:5000/api/status

# Detection test
curl -X POST http://localhost:5000/api/detect \
  -H "Content-Type: application/json" \
  -d '{"sensor": [0.0,0.38,0.19,0.12,0.0,-0.07,-0.49,0.80,0.0,0.0,0.0], "language": "en"}'
```

---

## 📊 Platform Comparison

| Feature | Vercel | Render |
|---------|--------|--------|
| **Flask Support** | ✅ Zero-config (since Oct 2025) | ✅ Native |
| **Ease of Setup** | ⭐⭐⭐⭐⭐ Very Easy | ⭐⭐⭐⭐ Easy |
| **Model File Support** | ⚠️ Size limits | ✅ Better support |
| **Free Tier** | ✅ Generous | ✅ Available (spins down) |
| **Auto-scaling** | ✅ Serverless | ✅ Vertical scaling |
| **Cold Starts** | ⚠️ Yes (serverless) | ✅ Minimal |
| **Preview Deployments** | ✅ Every branch | ❌ No |
| **Production Recommendation** | Good for APIs | Better for Flask apps |

---

## 🔐 Security Checklist

- [ ] Set a strong `SECRET_KEY` in production (never commit to git)
- [ ] Ensure `FLASK_DEBUG=false` in production
- [ ] Use HTTPS (automatically provided by both platforms)
- [ ] Consider adding rate limiting for API endpoints
- [ ] Implement proper authentication if needed
- [ ] Never commit `.env` file to git

---

## 🐛 Troubleshooting

### Vercel Deployment Fails

**Issue**: Build fails or deployment error
- Check Vercel logs in Dashboard
- Ensure `pyproject.toml` is present
- Verify Python version compatibility (>=3.9)

**Issue**: Model files too large
- Upload models to external storage (AWS S3, Cloudflare R2)
- Modify `app.py` to load models from URL

### Render Deployment Fails

**Issue**: Service fails to start
- Check Render logs in Dashboard
- Verify Procfile syntax
- Ensure all dependencies in requirements.txt

**Issue**: Application crashes
- Check Render logs for specific error
- Ensure PORT is read from environment variable

---

## 📝 Post-Deployment Steps

1. **Test the live API**
   ```bash
   curl https://your-app-url.vercel.app/api/status
   # or
   curl https://your-app-url.onrender.com/api/status
   ```

2. **Monitor performance**
   - Vercel: Dashboard → Analytics
   - Render: Dashboard → Metrics

3. **Set up monitoring** (optional)
   - Add error tracking (Sentry)
   - Set up uptime monitoring (UptimeRobot)

4. **Configure custom domain** (optional)
   - Both platforms support custom domains
   - Add CNAME records in DNS

---

## 🔄 CI/CD Setup (Optional)

### GitHub Actions for Automated Testing

Create `.github/workflows/test.yml`:

```yaml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python -m pytest  # if you add tests
```

---

## 📚 Additional Resources

- [Vercel Flask Documentation](https://vercel.com/docs/frameworks/backend/flask)
- [Render Python Flask Guide](https://render.com/docs/deploy-flask-apps)
- [Flask Deployment Documentation](https://flask.palletsprojects.com/en/latest/deploying/)

---

*Deployment guide updated November 2026*
