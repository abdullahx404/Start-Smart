# API Keys & Deployment Setup Guide

This document covers API key setup for both **local development** and **production deployment**.

---

## 🔐 Required API Keys

| Key | Purpose | Where to Get |
|-----|---------|--------------|
| Google Maps API | Display maps in frontend | [Google Cloud Console](https://console.cloud.google.com/) |
| Google Places API | Fetch business data | [Google Cloud Console](https://console.cloud.google.com/) |
| Groq API | AI-powered recommendations | [Groq Console](https://console.groq.com/) |

---

## 🖥️ Local Development Setup

### Frontend (Flutter Web)

1. Navigate to `frontend/web/`
2. Copy `env.example.js` to `env.js`
3. Edit `env.js` and add your Google Maps API key:

```javascript
const ENV_CONFIG = {
  GOOGLE_MAPS_API_KEY: 'AIzaSy_YOUR_ACTUAL_KEY_HERE'
};
```

**Note:** `env.js` is gitignored, so your key won't be committed.

### Backend (FastAPI)

1. Navigate to project root
2. Create/edit `.env` file:

```env
# Database (local)
DATABASE_URL=postgresql://postgres:root@localhost:5432/startsmart_dev

# API Keys
GOOGLE_PLACES_API_KEY=AIzaSy_YOUR_KEY_HERE
GROQ_API_KEY=gsk_YOUR_KEY_HERE

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
```

---

## 🚀 Production Deployment

### Option A: Render (Backend) + Vercel (Frontend)

This is the **recommended** free deployment option.

#### Step 1: Deploy Backend to Render

1. **Create Render Account:** Go to [render.com](https://render.com) and sign up
2. **Connect GitHub:** Link your GitHub account
3. **Create New Blueprint:**
   - Click "New" → "Blueprint"
   - Select your repository
   - Render will detect `render.yaml` automatically
4. **Set Environment Variables** in Render Dashboard:
   - `GOOGLE_PLACES_API_KEY`: Your Google Places API key
   - `GROQ_API_KEY`: Your Groq API key
5. **Deploy:** Click "Apply" to deploy
6. **Note Your API URL:** It will be like `https://startsmart-api.onrender.com`

#### Step 2: Update Frontend API URL

Edit `frontend/lib/utils/constants.dart`:

```dart
// Change this line to your Render URL
static const String _productionUrl = 'https://YOUR-RENDER-APP.onrender.com/api/v1';

// Set to true for production
const bool kIsProduction = true;
```

#### Step 3: Deploy Frontend to Vercel

1. **Create Vercel Account:** Go to [vercel.com](https://vercel.com) and sign up
2. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```
3. **Build Flutter Web:**
   ```bash
   cd frontend
   flutter build web --release
   ```
4. **Create env.js for production:**
   ```bash
   # In frontend/build/web/, create env.js with your API key
   echo 'const ENV_CONFIG = { GOOGLE_MAPS_API_KEY: "YOUR_KEY" };' > build/web/env.js
   ```
5. **Deploy to Vercel:**
   ```bash
   cd build/web
   vercel --prod
   ```

---

### Option B: Render Only (Both Backend & Frontend)

You can also deploy both on Render:

1. Deploy backend as above
2. Create a new "Static Site" on Render for frontend
3. Build command: `cd frontend && flutter build web --release`
4. Publish directory: `frontend/build/web`

---

## 📋 Environment Variables Summary

### For Render (Backend)

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Auto-set by Render |
| `GOOGLE_PLACES_API_KEY` | Google Places API key | Yes |
| `GROQ_API_KEY` | Groq LLM API key | Yes (for AI mode) |
| `ENVIRONMENT` | `production` | Yes |
| `LOG_LEVEL` | `INFO` or `WARNING` | Optional |

### For Vercel (Frontend)

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_MAPS_API_KEY` | In `env.js` file | Yes |

---

## 🔒 Security Notes

1. **Never commit API keys** to git
2. **Use environment variables** in production
3. **Restrict API keys** in Google Cloud Console:
   - Restrict by HTTP referrer for frontend keys
   - Restrict by IP for backend keys
4. **Rotate keys** if accidentally exposed

---

## 🧪 Testing Your Setup

### Test Backend Locally
```bash
cd backend
uvicorn api.main:app --reload --port 8000
# Visit: http://localhost:8000/docs
```

### Test Frontend Locally
```bash
cd frontend
flutter run -d chrome
```

### Test Production API
```bash
curl https://YOUR-RENDER-APP.onrender.com/api/v1/health
```

---

## 🆘 Troubleshooting

### "Google Maps API key invalid"
- Check if the key is correctly set in `env.js`
- Ensure Maps JavaScript API is enabled in Google Cloud Console

### "Database connection failed"
- Check `DATABASE_URL` is correctly set
- Ensure PostgreSQL is running (locally) or Render database is provisioned

### "GROQ API error"
- Check if `GROQ_API_KEY` is set
- The app falls back to "Fast Mode" if GROQ key is missing

---

## 📞 Getting API Keys

### Google Cloud (Maps & Places)
1. Go to [console.cloud.google.com](https://console.cloud.google.com/)
2. Create new project: "StartSmart"
3. Enable APIs:
   - Maps JavaScript API
   - Places API
4. Create credentials → API Key
5. (Optional) Restrict key for security

### Groq
1. Go to [console.groq.com](https://console.groq.com/)
2. Sign up (free tier available)
3. Create API key
4. Copy key starting with `gsk_`
