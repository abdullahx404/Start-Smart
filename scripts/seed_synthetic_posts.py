#!/usr/bin/env python3
"""
Synthetic Posts Database Seeder for StartSmart MVP
Phase 0: Load synthetic social media posts into social_posts table

This script reads the generated synthetic posts JSON file and bulk inserts
them into the database with validation and progress tracking.

Usage:
    python scripts/seed_synthetic_posts.py --input data/synthetic/social_posts_v1.json
    python scripts/seed_synthetic_posts.py --input data/synthetic/social_posts_v1.json --dry-run
"""

import json
import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict

try:
    import psycopg2
    from psycopg2.extras import execute_batch
    from dotenv import load_dotenv
except ImportError:
    print("❌ Error: Required packages not installed")
    print("   Run: pip install psycopg2-binary python-dotenv")
    sys.exit(1)


# ============================================================================
# Validation Functions
# ============================================================================

def validate_post(post: Dict[str, Any], index: int) -> tuple:
    """
    Validate a single post against the schema.
    
    Returns:
        (is_valid, error_message)
    """
    required_fields = [
        'post_id', 'source', 'timestamp', 'grid_id', 
        'post_type', 'engagement_score', 'is_simulated'
    ]
    
    # Check required fields
    for field in required_fields:
        if field not in post:
            return False, f"Missing required field: {field}"
    
    # Validate data types and values
    if not isinstance(post['post_id'], str) or not post['post_id']:
        return False, "post_id must be non-empty string"
    
    if post['source'] not in ['instagram', 'reddit', 'simulated']:
        return False, f"Invalid source: {post['source']}"
    
    if post['post_type'] not in ['demand', 'complaint', 'mention', None]:
        return False, f"Invalid post_type: {post['post_type']}"
    
    if not isinstance(post['engagement_score'], int) or post['engagement_score'] < 0:
        return False, "engagement_score must be non-negative integer"
    
    if not isinstance(post['is_simulated'], bool):
        return False, "is_simulated must be boolean"
    
    # Validate coordinates if present
    if 'lat' in post and post['lat'] is not None:
        if not isinstance(post['lat'], (int, float)) or not (-90 <= post['lat'] <= 90):
            return False, f"Invalid latitude: {post['lat']}"
    
    if 'lon' in post and post['lon'] is not None:
        if not isinstance(post['lon'], (int, float)) or not (-180 <= post['lon'] <= 180):
            return False, f"Invalid longitude: {post['lon']}"
    
    # Validate timestamp format
    try:
        datetime.fromisoformat(post['timestamp'].replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return False, f"Invalid timestamp format: {post['timestamp']}"
    
    return True, None


def validate_posts_batch(posts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate all posts and return statistics.
    
    Returns:
        Dictionary with validation results
    """
    valid_posts = []
    errors = []
    
    for i, post in enumerate(posts):
        is_valid, error_msg = validate_post(post, i)
        if is_valid:
            valid_posts.append(post)
        else:
            errors.append({
                'index': i,
                'post_id': post.get('post_id', 'unknown'),
                'error': error_msg
            })
    
    return {
        'total': len(posts),
        'valid': len(valid_posts),
        'invalid': len(errors),
        'valid_posts': valid_posts,
        'errors': errors
    }


# ============================================================================
# Statistics Functions
# ============================================================================

def calculate_statistics(posts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate summary statistics for posts."""
    stats = {
        'total_posts': len(posts),
        'by_type': defaultdict(int),
        'by_source': defaultdict(int),
        'by_grid': defaultdict(int),
        'simulated_count': 0,
        'with_coordinates': 0,
        'engagement_total': 0
    }
    
    for post in posts:
        stats['by_type'][post.get('post_type', 'unknown')] += 1
        stats['by_source'][post.get('source', 'unknown')] += 1
        stats['by_grid'][post.get('grid_id', 'unknown')] += 1
        
        if post.get('is_simulated'):
            stats['simulated_count'] += 1
        
        if post.get('lat') is not None and post.get('lon') is not None:
            stats['with_coordinates'] += 1
        
        stats['engagement_total'] += post.get('engagement_score', 0)
    
    if stats['total_posts'] > 0:
        stats['engagement_avg'] = stats['engagement_total'] / stats['total_posts']
    else:
        stats['engagement_avg'] = 0
    
    return stats


def print_statistics(stats: Dict[str, Any]):
    """Print formatted statistics."""
    print("\n" + "=" * 70)
    print("📊 Dataset Statistics")
    print("=" * 70)
    
    print(f"\nTotal posts: {stats['total_posts']}")
    print(f"Simulated posts: {stats['simulated_count']} ({stats['simulated_count']/stats['total_posts']*100:.1f}%)")
    print(f"Posts with coordinates: {stats['with_coordinates']}")
    print(f"Average engagement: {stats['engagement_avg']:.1f}")
    
    print(f"\nBy post type:")
    for ptype, count in sorted(stats['by_type'].items()):
        pct = (count / stats['total_posts'] * 100) if stats['total_posts'] > 0 else 0
        print(f"  {ptype}: {count} ({pct:.1f}%)")
    
    print(f"\nBy source:")
    for source, count in sorted(stats['by_source'].items()):
        pct = (count / stats['total_posts'] * 100) if stats['total_posts'] > 0 else 0
        print(f"  {source}: {count} ({pct:.1f}%)")
    
    print(f"\nPosts per grid:")
    for grid_id, count in sorted(stats['by_grid'].items()):
        print(f"  {grid_id}: {count} posts")


# ============================================================================
# Database Operations
# ============================================================================

def get_database_connection(database_url: str):
    """Create database connection from DATABASE_URL."""
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except psycopg2.Error as e:
        print(f"❌ Database connection failed: {e}")
        raise


def insert_posts(conn, posts: List[Dict[str, Any]], dry_run: bool = False) -> int:
    """
    Bulk insert posts into database with progress tracking.
    
    Args:
        conn: Database connection
        posts: List of validated post dictionaries
        dry_run: If True, preview SQL without executing
    
    Returns:
        Number of rows inserted
    """
    if not posts:
        print("⚠️  No posts to insert")
        return 0
    
    insert_sql = """
        INSERT INTO social_posts (
            post_id, source, text, timestamp, lat, lon, grid_id,
            post_type, engagement_score, is_simulated
        ) VALUES (
            %(post_id)s, %(source)s, %(text)s, %(timestamp)s,
            %(lat)s, %(lon)s, %(grid_id)s, %(post_type)s,
            %(engagement_score)s, %(is_simulated)s
        )
        ON CONFLICT (post_id) DO UPDATE SET
            source = EXCLUDED.source,
            text = EXCLUDED.text,
            timestamp = EXCLUDED.timestamp,
            lat = EXCLUDED.lat,
            lon = EXCLUDED.lon,
            grid_id = EXCLUDED.grid_id,
            post_type = EXCLUDED.post_type,
            engagement_score = EXCLUDED.engagement_score,
            is_simulated = EXCLUDED.is_simulated
    """
    
    if dry_run:
        print("\n🔍 DRY RUN - Preview SQL (first 3 posts):")
        print("-" * 70)
        print(insert_sql)
        print("\nSample data:")
        for i, post in enumerate(posts[:3]):
            print(f"\n  Post {i+1}: {post['post_id']}")
            print(f"    Source: {post['source']}")
            print(f"    Type: {post['post_type']}")
            print(f"    Grid: {post['grid_id']}")
            print(f"    Text: {post.get('text', 'N/A')[:50]}...")
        print(f"\n  ... and {len(posts) - 3} more posts")
        print("-" * 70)
        return len(posts)
    
    try:
        cursor = conn.cursor()
        total = len(posts)
        batch_size = 100
        
        print(f"\n💾 Inserting {total} posts in batches of {batch_size}...")
        
        # Simple progress tracking
        for i in range(0, total, batch_size):
            batch = posts[i:i + batch_size]
            execute_batch(cursor, insert_sql, batch, page_size=batch_size)
            
            progress = min(i + batch_size, total)
            percentage = (progress / total) * 100
            bar_length = 40
            filled = int(bar_length * progress / total)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            print(f"  [{bar}] {progress}/{total} ({percentage:.1f}%)", end='\r')
        
        print()  # New line after progress bar
        
        rows_inserted = cursor.rowcount
        cursor.close()
        
        return rows_inserted
        
    except psycopg2.Error as e:
        print(f"\n❌ Database insert failed: {e}")
        raise


def verify_insertion(conn, expected_count: int) -> Dict[str, Any]:
    """Verify that posts were inserted correctly."""
    try:
        cursor = conn.cursor()
        
        # Count total posts
        cursor.execute("SELECT COUNT(*) FROM social_posts")
        total_count = cursor.fetchone()[0]
        
        # Count simulated posts
        cursor.execute("SELECT COUNT(*) FROM social_posts WHERE is_simulated = TRUE")
        simulated_count = cursor.fetchone()[0]
        
        # Get distribution by type
        cursor.execute("""
            SELECT post_type, COUNT(*) as count
            FROM social_posts
            WHERE is_simulated = TRUE
            GROUP BY post_type
            ORDER BY count DESC
        """)
        type_distribution = cursor.fetchall()
        
        cursor.close()
        
        return {
            'total_posts': total_count,
            'simulated_posts': simulated_count,
            'expected_posts': expected_count,
            'match': simulated_count == expected_count,
            'type_distribution': type_distribution
        }
        
    except psycopg2.Error as e:
        print(f"⚠️  Verification query failed: {e}")
        return {
            'total_posts': 0,
            'simulated_posts': 0,
            'expected_posts': expected_count,
            'match': False
        }


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Seed social_posts table from synthetic data JSON',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path to synthetic posts JSON file'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview SQL without executing (no database changes)'
    )
    
    parser.add_argument(
        '--database-url',
        type=str,
        default=None,
        help='PostgreSQL connection string (default: from DATABASE_URL env var)'
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Get database URL
    database_url = args.database_url or os.getenv('DATABASE_URL')
    if not database_url and not args.dry_run:
        print("❌ Error: DATABASE_URL not found")
        print("   Set DATABASE_URL environment variable or use --database-url")
        return 1
    
    print("=" * 70)
    print("StartSmart Synthetic Posts Seeder - Phase 0")
    print("=" * 70)
    print()
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No database changes will be made")
        print()
    
    # Load JSON file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_path}")
        return 1
    
    print(f"📄 Loading posts from: {input_path}")
    print(f"   File size: {input_path.stat().st_size / 1024:.1f} KB")
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            posts_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in input file: {e}")
        return 1
    
    if not isinstance(posts_data, list):
        print("❌ Error: JSON file must contain an array of posts")
        return 1
    
    print(f"   Loaded: {len(posts_data)} posts")
    print()
    
    # Validate posts
    print("✓ Validating posts...")
    validation = validate_posts_batch(posts_data)
    
    print(f"   Total: {validation['total']}")
    print(f"   Valid: {validation['valid']}")
    print(f"   Invalid: {validation['invalid']}")
    
    if validation['invalid'] > 0:
        print("\n⚠️  Validation errors found:")
        for error in validation['errors'][:5]:  # Show first 5 errors
            print(f"   - Post {error['index']} ({error['post_id']}): {error['error']}")
        if validation['invalid'] > 5:
            print(f"   ... and {validation['invalid'] - 5} more errors")
        
        print("\n❌ Aborting due to validation errors")
        return 1
    
    print("   ✓ All posts valid")
    
    # Calculate statistics
    stats = calculate_statistics(validation['valid_posts'])
    print_statistics(stats)
    
    # Connect to database (unless dry-run)
    conn = None
    if not args.dry_run:
        print("\n🔌 Connecting to database...")
        try:
            conn = get_database_connection(database_url)
            print("   ✓ Connected successfully")
        except Exception as e:
            print(f"   ✗ Connection failed: {e}")
            return 1
    
    # Insert posts
    try:
        if not args.dry_run and conn:
            conn.autocommit = False
        
        rows_affected = insert_posts(conn, validation['valid_posts'], dry_run=args.dry_run)
        
        if not args.dry_run and conn:
            conn.commit()
            print(f"   ✓ Inserted {rows_affected} rows")
            
            # Verify insertion
            print("\n🔍 Verifying insertion...")
            verification = verify_insertion(conn, validation['valid'])
            
            print(f"   Database total (all posts): {verification['total_posts']}")
            print(f"   Simulated posts: {verification['simulated_posts']}")
            print(f"   Expected: {verification['expected_posts']}")
            
            if verification['match']:
                print("   ✓ Verification PASSED")
            else:
                print("   ⚠️  Verification FAILED - count mismatch")
            
            print("\n   Post type distribution (simulated only):")
            for post_type, count in verification['type_distribution']:
                print(f"     - {post_type}: {count}")
            
        else:
            print(f"\n   Would insert {rows_affected} rows (dry-run)")
        
        print("\n" + "=" * 70)
        print("✅ Post seeding complete!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error during insertion: {e}")
        if conn and not args.dry_run:
            conn.rollback()
            print("   Transaction rolled back")
        return 1
        
    finally:
        if conn:
            conn.close()
            print("\n🔌 Database connection closed")
    
    return 0


if __name__ == "__main__":
    exit(main())
