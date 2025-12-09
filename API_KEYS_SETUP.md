# API Keys Setup Guide

This document lists all the API keys required for the StartSmart application and where to add them.

---

## ⚠️ IMPORTANT: Never Commit API Keys to Git

Before committing any changes, make sure:
1. API keys are NOT hardcoded in the source files
2. `.env` files are listed in `.gitignore`
3. Only placeholder values like `YOUR_API_KEY_HERE` are in the repository

---

## Required API Keys

### 1. Google Maps JavaScript API Key (Frontend)

**Purpose:** Used to display Google Maps in the Flutter web application.

**File:** `frontend/web/index.html`  
**Line:** 36

**How to add:**
1. Open `frontend/web/index.html`
2. Find line 36 with the Google Maps script tag
3. Replace `YOUR_GOOGLE_MAPS_API_KEY` with your actual API key

```html
<!-- Before -->
<script src="https://maps.googleapis.com/maps/api/js?key=YOUR_GOOGLE_MAPS_API_KEY"></script>

<!-- After (example) -->
<script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyYOUR_ACTUAL_KEY_HERE"></script>
```

**How to get this key:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable "Maps JavaScript API"
4. Go to Credentials → Create Credentials → API Key
5. Restrict the key to "Maps JavaScript API" for security

---

### 2. Google Places API Key (Backend)

**Purpose:** Used to fetch business data from Google Places API.

**File:** `backend/.env`  
**Variable:** `GOOGLE_PLACES_API_KEY`

**How to add:**
1. Open or create `backend/.env`
2. Add or update the following line:

```env
GOOGLE_PLACES_API_KEY=your_google_places_api_key_here
```

**How to get this key:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable "Places API" and "Places API (New)"
3. Go to Credentials → Create Credentials → API Key
4. Restrict the key to "Places API" for security

---

### 3. Groq API Key (Backend - For AI/LLM Features)

**Purpose:** Used for AI-powered location analysis and recommendations using Groq LLM.

**File:** `backend/.env`  
**Variable:** `GROQ_API_KEY`

**How to add:**
1. Open or create `backend/.env`
2. Add the following line:

```env
GROQ_API_KEY=gsk_your_groq_api_key_here
```

**How to get this key:**
1. Go to [Groq Console](https://console.groq.com/)
2. Sign up or log in
3. Go to API Keys section
4. Create a new API key
5. Copy the key (starts with `gsk_`)

**Note:** If GROQ_API_KEY is not set, the application will use "Fast Mode" (rule-based analysis) instead of "AI Mode" (LLM-powered analysis).

---

## Complete Backend `.env` File Example

Create a file at `backend/.env` with the following content:

```env
# StartSmart Backend - Environment Variables

# Database Configuration
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/startsmart_dev

# Google Places API (for fetching business data)
GOOGLE_PLACES_API_KEY=your_google_places_api_key_here

# Groq API (for AI-powered recommendations)
GROQ_API_KEY=gsk_your_groq_api_key_here

# Application Environment
ENVIRONMENT=development

# Logging
LOG_LEVEL=INFO
```

---

## Files Summary

| API Key | File Location | Line/Variable |
|---------|---------------|---------------|
| Google Maps JS API | `frontend/web/index.html` | Line 36 |
| Google Places API | `backend/.env` | `GOOGLE_PLACES_API_KEY` |
| Groq API | `backend/.env` | `GROQ_API_KEY` |

---

## Security Checklist

- [ ] `backend/.env` is in `.gitignore`
- [ ] No actual API keys in source code
- [ ] API keys are restricted to specific APIs in Google Cloud Console
- [ ] API keys have usage quotas/limits set

---

## Troubleshooting

### Google Maps not loading
- Check if the API key is correctly placed in `index.html`
- Verify the API key is enabled for "Maps JavaScript API"
- Check browser console for API key errors

### Backend API errors
- Check if `.env` file exists in `backend/` directory
- Verify environment variables are loaded (check backend logs)
- Make sure the API key has the correct permissions

### AI Mode not working
- Verify `GROQ_API_KEY` is set in `backend/.env`
- Check if the key starts with `gsk_`
- The app will fall back to Fast Mode if Groq key is missing

---

**Last Updated:** December 7, 2025
