"""
Vercel Serverless Function Entry Point

This file is the entry point for Vercel serverless deployment.
It exposes the FastAPI app as a Vercel serverless function.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment variable to skip database check
os.environ["SKIP_DB_CHECK"] = "true"

# Import the FastAPI app
from api.main import app

# Vercel expects a handler named 'app' or we can use the ASGI handler
handler = app
