#!/usr/bin/env python3
"""
Generate synthetic social media posts for any neighborhood

Usage:
    python scripts/generate_synthetic_posts_v2.py --neighborhood "Clifton Block 2" --category Gym
    python scripts/generate_synthetic_posts_v2.py --all  # Generate for all neighborhoods
"""

import json
import random
import uuid
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

TEMPLATES = {
    "Gym": {
        "demand": [
            "Looking for a good gym in {loc}. Any recommendations?",
            "Need a gym near {loc} with proper equipment",
            "Anyone know a good fitness center in {loc}?",
            "Searching for affordable gym memberships in {loc}",
            "Want to join a gym in {loc}, suggestions?"
        ],
        "complaint": [
            "No good gyms in {loc} at all",
            "Why are there no proper gyms in {loc}?",
            "The gym situation in {loc} is terrible",
            "Can't find a decent gym in {loc}",
            "Looking for better gym options in {loc}"
        ],
        "mention": [
            "Morning workout done! #fitness #gym #{tag}",
            "Leg day at the gym #{tag}",
            "Great session today! #{tag} #fitness",
            "New PR! #{tag} #gym #strength",
            "Cardio done ✓ #{tag} #workout"
        ]
    },
    "Cafe": {
        "demand": [
            "Looking for a good cafe in {loc}. Suggestions?",
            "Need a quiet cafe near {loc} with WiFi",
            "Anyone know good coffee shops in {loc}?",
            "Where can I find a cozy cafe in {loc}?",
            "Best cafe for working in {loc}?"
        ],
        "complaint": [
            "No good cafes in {loc}!",
            "Why are there no decent coffee shops in {loc}?",
            "The cafe options in {loc} are disappointing",
            "Can't find a proper cafe in {loc}",
            "Need better cafes in {loc}"
        ],
        "mention": [
            "Coffee break! #{tag} #cafe",
            "Perfect latte today #{tag}",
            "Love this cafe! #{tag} #coffee",
            "Great cappuccino #{tag} #coffeelover",
            "Working from cafe #{tag} #remote"
        ]
    }
}


def get_grids_from_db(neighborhood_name=None):
    """Fetch grid cells from database."""
    database_url = os.getenv("DATABASE_URL")
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    
    if neighborhood_name:
        cursor.execute("""
            SELECT grid_id, neighborhood, lat_north, lat_south, lon_east, lon_west, 
                   lat_center, lon_center
            FROM grid_cells
            WHERE neighborhood = %s
            ORDER BY grid_id
        """, (neighborhood_name,))
    else:
        cursor.execute("""
            SELECT grid_id, neighborhood, lat_north, lat_south, lon_east, lon_west,
                   lat_center, lon_center
            FROM grid_cells
            ORDER BY neighborhood, grid_id
        """)
    
    grids = []
    for row in cursor.fetchall():
        grids.append({
            "grid_id": row[0],
            "neighborhood": row[1],
            "lat_north": float(row[2]),
            "lat_south": float(row[3]),
            "lon_east": float(row[4]),
            "lon_west": float(row[5]),
            "lat_center": float(row[6]),
            "lon_center": float(row[7])
        })
    
    cursor.close()
    conn.close()
    
    return grids


def generate_posts(grids, category, posts_per_grid=50, seed=None):
    """Generate synthetic posts for given grids."""
    if seed:
        random.seed(seed)
    
    posts = []
    
    for idx, grid in enumerate(grids):
        # Determine opportunity level (high/medium/low) based on position
        # First 2 grids = high, last 2 = low, rest = medium
        total_grids = len(grids)
        if idx < 2:
            opp = "high"
        elif idx >= total_grids - 2:
            opp = "low"
        else:
            opp = "medium"
        
        # Adjust post count based on opportunity level
        count = int(posts_per_grid * (1.5 if opp == "high" else 0.6 if opp == "low" else 1.0))
        
        # Extract neighborhood tag (e.g., "Clifton" from "Clifton Block 2")
        neighborhood_tag = grid['neighborhood'].split()[0]
        
        for _ in range(count):
            # Choose post type with weights based on opportunity
            if opp == "high":
                weights = [0.40, 0.40, 0.20]  # more demand/complaint
            else:
                weights = [0.60, 0.25, 0.15]  # mostly mentions
            
            ptype = random.choices(["mention", "demand", "complaint"], weights=weights)[0]
            
            # Generate text
            text = random.choice(TEMPLATES[category][ptype]).format(
                loc=grid['neighborhood'],
                tag=neighborhood_tag
            )
            
            # Random location within grid bounds
            lat = round(
                grid['lat_south'] + random.random() * (grid['lat_north'] - grid['lat_south']),
                6
            )
            lon = round(
                grid['lon_west'] + random.random() * (grid['lon_east'] - grid['lon_west']),
                6
            )
            
            # Engagement score: higher for demand/complaint, lower for mentions
            if opp == "high":
                engagement = random.randint(20 if ptype == "mention" else 50, 100)
            else:
                engagement = random.randint(5 if ptype == "mention" else 10, 50)
            
            posts.append({
                "post_id": str(uuid.uuid4()),
                "source": "simulated",
                "text": text,
                "timestamp": (datetime.utcnow() - timedelta(days=random.randint(0, 90))).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "lat": lat,
                "lon": lon,
                "grid_id": grid['grid_id'],
                "post_type": ptype,
                "engagement_score": engagement,
                "is_simulated": True
            })
    
    return posts


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic social media posts for neighborhoods",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate posts for specific neighborhood + category
  python scripts/generate_synthetic_posts_v2.py --neighborhood "Clifton Block 2" --category Gym
  
  # Generate for all neighborhoods and categories
  python scripts/generate_synthetic_posts_v2.py --all
  
  # Custom post count
  python scripts/generate_synthetic_posts_v2.py --neighborhood "DHA Phase 2" --category Cafe --posts 100
        """
    )
    
    parser.add_argument("--neighborhood", type=str, help="Neighborhood name (e.g., 'Clifton Block 2')")
    parser.add_argument("--category", type=str, choices=["Gym", "Cafe"], help="Business category")
    parser.add_argument("--all", action="store_true", help="Generate for all neighborhoods and categories")
    parser.add_argument("--posts", type=int, default=50, help="Posts per grid (default: 50)")
    parser.add_argument("--output", type=str, default="data/synthetic/", help="Output directory")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--insert-db", action="store_true", help="Insert directly into database")
    
    args = parser.parse_args()
    
    if not args.all and (not args.neighborhood or not args.category):
        parser.error("Either --all or both --neighborhood and --category must be specified")
    
    print("=" * 70)
    print("SYNTHETIC SOCIAL POSTS GENERATOR - Phase 0")
    print("=" * 70)
    
    if args.all:
        print("\n🔄 Generating posts for ALL neighborhoods and categories...")
        grids = get_grids_from_db()
        
        # Group by neighborhood
        neighborhoods = {}
        for grid in grids:
            hood = grid['neighborhood']
            if hood not in neighborhoods:
                neighborhoods[hood] = []
            neighborhoods[hood].append(grid)
        
        all_posts = []
        for hood, hood_grids in neighborhoods.items():
            for category in ["Gym", "Cafe"]:
                print(f"\n📍 {hood} - {category}")
                posts = generate_posts(hood_grids, category, args.posts, args.seed)
                all_posts.extend(posts)
                print(f"   Generated {len(posts)} posts")
        
        output_file = "social_posts_all_v2.json"
    else:
        print(f"\n📍 Neighborhood: {args.neighborhood}")
        print(f"🏷️  Category: {args.category}")
        
        grids = get_grids_from_db(args.neighborhood)
        
        if not grids:
            print(f"\n❌ Error: No grids found for neighborhood '{args.neighborhood}'")
            return 1
        
        print(f"📊 Found {len(grids)} grid cells")
        
        all_posts = generate_posts(grids, args.category, args.posts, args.seed)
        
        # Sanitize filename
        hood_safe = args.neighborhood.lower().replace(" ", "_")
        output_file = f"{hood_safe}_{args.category.lower()}_posts.json"
    
    # Save to file
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_file
    
    with open(output_path, "w") as f:
        json.dump(all_posts, f, indent=2)
    
    print(f"\n✅ Generated {len(all_posts)} total posts")
    print(f"💾 Saved to: {output_path}")
    
    # Insert into database if requested
    if args.insert_db:
        print(f"\n📥 Inserting posts into database...")
        database_url = os.getenv("DATABASE_URL")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        inserted = 0
        for post in all_posts:
            try:
                cursor.execute("""
                    INSERT INTO social_posts 
                    (post_id, source, text, timestamp, lat, lon, grid_id, 
                     post_type, engagement_score, is_simulated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (post_id) DO NOTHING
                """, (
                    post['post_id'],
                    post['source'],
                    post['text'],
                    post['timestamp'],
                    post['lat'],
                    post['lon'],
                    post['grid_id'],
                    post['post_type'],
                    post['engagement_score'],
                    post['is_simulated']
                ))
                inserted += 1
            except Exception as e:
                print(f"   ⚠️  Error inserting post: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Inserted {inserted} posts into database")
    
    print("\n" + "=" * 70)
    print("✅ GENERATION COMPLETE")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
