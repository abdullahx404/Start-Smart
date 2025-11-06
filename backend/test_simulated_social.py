"""
Quick test script for SimulatedSocialAdapter

This script tests the adapter without requiring complex imports.
Run from project root: python backend/test_simulated_social.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Now imports should work
from backend.src.adapters.simulated_social_adapter import create_adapter

print("=" * 80)
print("SIMULATED SOCIAL ADAPTER - QUICK TEST")
print("=" * 80)
print()

# Test bounds (DHA Phase 2, Cell-07)
test_bounds = {
    'lat_north': 24.8320,
    'lat_south': 24.8260,
    'lon_east': 67.0640,
    'lon_west': 67.0580
}

try:
    # Create adapter
    print("Creating SimulatedSocialAdapter...")
    adapter = create_adapter()
    print(f"✓ Adapter created: {adapter.get_source_name()}")
    print()
    
    # Test: Fetch posts
    print("TEST: Fetch simulated posts (Gym, 90 days)")
    print("-" * 80)
    
    posts = adapter.fetch_social_posts(
        category="Gym",
        bounds=test_bounds,
        days=90
    )
    
    print(f"✓ Found {len(posts)} posts in last 90 days")
    
    if posts:
        print("\nFirst 5 posts:")
        for i, post in enumerate(posts[:5], 1):
            text_preview = post.text[:60] if post.text else "No text"
            print(f"  {i}. [{post.source}] {post.post_type or 'N/A'}: {text_preview}...")
            print(f"     Engagement: {post.engagement_score}, Location: ({post.lat:.4f}, {post.lon:.4f})")
    
    print()
    print("=" * 80)
    print("TEST COMPLETE - Adapter is working!")
    print("=" * 80)
    
except Exception as e:
    print(f"\n✗ TEST FAILED: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
