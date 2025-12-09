"""
Data Adapters Module

This module contains adapter implementations that extend BaseAdapter from
contracts/base_adapter.py. Each adapter is responsible for fetching data
from a specific external source and normalizing it to our data models.

Available Adapters:
    - GooglePlacesAdapter: Fetches business data from Google Places API
    - SimulatedSocialAdapter: Reads synthetic social posts from database

Factory Functions:
    - create_adapter: Creates GooglePlacesAdapter with API key from env
    - create_social_adapter: Creates SimulatedSocialAdapter instance
"""

from .google_places_adapter import GooglePlacesAdapter, create_adapter
from .simulated_social_adapter import SimulatedSocialAdapter, create_adapter as create_social_adapter

__all__ = [
    "GooglePlacesAdapter",
    "create_adapter",
    "SimulatedSocialAdapter",
    "create_social_adapter",
]
