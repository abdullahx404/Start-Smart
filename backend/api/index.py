"""
Vercel Serverless Function Entry Point

This file is the entry point for Vercel serverless deployment.
It exposes the FastAPI app as a Vercel serverless function.
"""

import sys
import os

# Set environment variable to skip database check BEFORE any imports
os.environ["SKIP_DB_CHECK"] = "true"

# Add the parent directory (backend) to the Python path for imports
# This is needed because Vercel runs from the backend directory
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import the FastAPI app
from api.main import app

# Vercel expects the app to be named 'app' for ASGI
# This is the handler that Vercel will use
