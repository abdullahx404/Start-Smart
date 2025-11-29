"""
Verify data distribution for Phase 2 Analytics & Scoring Engine.

This script queries the database to understand:
- Business distribution across grids
- Social post distribution across grids
- Grids with zero businesses
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.database.connection import get_session
from src.database.models import BusinessModel, SocialPostModel, GridCellModel
from sqlalchemy import func


def main():
    with get_session() as session:
        
        print("\n" + "="*70)
        print("PHASE 2 DATA VERIFICATION - ANALYTICS & SCORING ENGINE")
        print("="*70)
        
        # 1. Businesses per grid and category
        print("\n📊 BUSINESSES PER GRID (by Category)")
        print("-" * 70)
        business_results = (
            session.query(
            BusinessModel.grid_id,
            BusinessModel.category,
            func.count(BusinessModel.business_id).label('count')
        )
        .group_by(BusinessModel.grid_id, BusinessModel.category)
        .order_by(BusinessModel.grid_id, BusinessModel.category)
        .all()
    )
    
    if business_results:
        print(f"{'Grid ID':<30} {'Category':<15} {'Count':>10}")
        print("-" * 70)
        for row in business_results:
            grid_id = row.grid_id if row.grid_id else "NULL"
            category = row.category if row.category else "NULL"
            print(f"{grid_id:<30} {category:<15} {row.count:>10}")
    else:
        print("⚠️  No businesses found in database")
    
    total_businesses = session.query(func.count(BusinessModel.business_id)).scalar()
    print(f"\n{'TOTAL BUSINESSES:':<45} {total_businesses:>10}")
    
    # 2. Social posts per grid and post type
    print("\n\n📱 SOCIAL POSTS PER GRID (by Post Type)")
    print("-" * 70)
    post_results = (
        session.query(
            SocialPostModel.grid_id,
            SocialPostModel.post_type,
            func.count(SocialPostModel.post_id).label('count')
        )
        .group_by(SocialPostModel.grid_id, SocialPostModel.post_type)
        .order_by(SocialPostModel.grid_id, SocialPostModel.post_type)
        .all()
    )
    
    if post_results:
        print(f"{'Grid ID':<30} {'Post Type':<15} {'Count':>10}")
        print("-" * 70)
        for row in post_results:
            post_type = row.post_type if row.post_type else "None"
            print(f"{row.grid_id:<30} {post_type:<15} {row.count:>10}")
    else:
        print("⚠️  No social posts found in database")
    
    total_posts = session.query(func.count(SocialPostModel.post_id)).scalar()
    print(f"\n{'TOTAL SOCIAL POSTS:':<45} {total_posts:>10}")
    
    # 3. Grids with zero businesses
    print("\n\n🔍 GRIDS WITH ZERO BUSINESSES")
    print("-" * 70)
    grids_without_businesses = (
        session.query(GridCellModel.grid_id)
        .outerjoin(BusinessModel, GridCellModel.grid_id == BusinessModel.grid_id)
        .group_by(GridCellModel.grid_id)
        .having(func.count(BusinessModel.business_id) == 0)
        .all()
    )
    
    if grids_without_businesses:
        for row in grids_without_businesses:
            print(f"  - {row.grid_id}")
        print(f"\nTotal grids with 0 businesses: {len(grids_without_businesses)}")
    else:
        print("✅ All grids have at least one business")
    
    # 4. Summary statistics
    print("\n\n📈 SUMMARY STATISTICS")
    print("-" * 70)
    
    # Total grids
    total_grids = session.query(func.count(GridCellModel.grid_id)).scalar()
    print(f"Total grid cells: {total_grids}")
    
    # Grids with businesses
    grids_with_businesses = (
        session.query(func.count(func.distinct(BusinessModel.grid_id)))
        .filter(BusinessModel.grid_id.isnot(None))
        .scalar()
    )
    print(f"Grids with businesses: {grids_with_businesses}")
    
    # Grids with social posts
    grids_with_posts = (
        session.query(func.count(func.distinct(SocialPostModel.grid_id)))
        .filter(SocialPostModel.grid_id.isnot(None))
        .scalar()
    )
    print(f"Grids with social posts: {grids_with_posts}")
    
    # Average businesses per grid (excluding empty grids)
    if grids_with_businesses > 0:
        avg_businesses = total_businesses / grids_with_businesses
        print(f"Average businesses per grid (with data): {avg_businesses:.2f}")
    
    # Average posts per grid (excluding empty grids)
    if grids_with_posts > 0:
        avg_posts = total_posts / grids_with_posts
        print(f"Average social posts per grid (with data): {avg_posts:.2f}")
    
    # Categories present
    categories = (
        session.query(func.distinct(BusinessModel.category))
        .filter(BusinessModel.category.isnot(None))
        .all()
    )
    print(f"\nCategories in database: {', '.join([c[0] for c in categories]) if categories else 'None'}")
    
    print("\n" + "="*70)
    print("✅ DATA VERIFICATION COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
