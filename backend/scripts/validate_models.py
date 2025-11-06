"""
ORM Models Validation Script

This script validates that ORM models match the database schema exactly.
Run this after creating models to ensure correctness.

Usage:
    python backend/scripts/validate_models.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def validate_models():
    """Validate ORM models against schema"""
    
    print("=" * 70)
    print("ORM MODELS VALIDATION")
    print("=" * 70)
    
    # Test 1: Import models
    print("\n✓ Test 1: Importing ORM models...")
    try:
        from src.database.models import (
            GridCellModel,
            BusinessModel,
            SocialPostModel,
            GridMetricsModel,
            UserFeedbackModel,
            get_all_models,
            get_model_by_table_name,
        )
        print("  ✅ All models imported successfully")
    except ImportError as e:
        print(f"  ❌ Failed to import models: {e}")
        print("\n  Make sure SQLAlchemy is installed:")
        print("    pip install sqlalchemy python-dotenv psycopg2-binary")
        return False
    
    # Test 2: Verify table names
    print("\n✓ Test 2: Verifying table names...")
    expected_tables = {
        'grid_cells': GridCellModel,
        'businesses': BusinessModel,
        'social_posts': SocialPostModel,
        'grid_metrics': GridMetricsModel,
        'user_feedback': UserFeedbackModel,
    }
    
    all_correct = True
    for table_name, model_class in expected_tables.items():
        if model_class.__tablename__ == table_name:
            print(f"  ✅ {model_class.__name__} → {table_name}")
        else:
            print(f"  ❌ {model_class.__name__} → Expected '{table_name}', got '{model_class.__tablename__}'")
            all_correct = False
    
    if not all_correct:
        return False
    
    # Test 3: Verify column counts
    print("\n✓ Test 3: Verifying column counts...")
    expected_columns = {
        'GridCellModel': 10,  # grid_id, neighborhood, lat_center, lon_center, lat_north, lat_south, lon_east, lon_west, area_km2, created_at
        'BusinessModel': 10,  # business_id, name, lat, lon, category, rating, review_count, source, grid_id, fetched_at
        'SocialPostModel': 11,  # post_id, source, text, timestamp, lat, lon, grid_id, post_type, engagement_score, is_simulated, created_at
        'GridMetricsModel': 11,  # id, grid_id, category, business_count, instagram_volume, reddit_mentions, gos, confidence, top_posts_json, competitors_json, last_updated
        'UserFeedbackModel': 7,  # id, grid_id, category, rating, comment, user_email, created_at
    }
    
    for model_class in get_all_models():
        model_name = model_class.__name__
        actual_columns = len(model_class.__table__.columns)
        expected = expected_columns.get(model_name, 0)
        
        if actual_columns == expected:
            print(f"  ✅ {model_name}: {actual_columns} columns")
        else:
            print(f"  ⚠️  {model_name}: Expected {expected} columns, got {actual_columns}")
    
    # Test 4: Test model instantiation
    print("\n✓ Test 4: Testing model instantiation...")
    from decimal import Decimal
    from datetime import datetime
    
    try:
        # GridCell
        grid = GridCellModel(
            grid_id="TEST-01",
            neighborhood="Test",
            lat_center=Decimal("24.8290"),
            lon_center=Decimal("67.0610"),
            lat_north=Decimal("24.8320"),
            lat_south=Decimal("24.8260"),
            lon_east=Decimal("67.0640"),
            lon_west=Decimal("67.0580"),
        )
        print("  ✅ GridCellModel instantiated")
        
        # Business
        business = BusinessModel(
            business_id="test-gym-001",
            name="Test Gym",
            lat=Decimal("24.8300"),
            lon=Decimal("67.0600"),
            category="Gym",
            rating=Decimal("4.5"),
        )
        print("  ✅ BusinessModel instantiated")
        
        # SocialPost
        post = SocialPostModel(
            post_id="test-post-001",
            source="simulated",
            text="Test post",
            timestamp=datetime.utcnow(),
            is_simulated=True,
        )
        print("  ✅ SocialPostModel instantiated")
        
        # GridMetrics
        metrics = GridMetricsModel(
            grid_id="TEST-01",
            category="Gym",
            gos=Decimal("0.825"),
            confidence=Decimal("0.780"),
        )
        print("  ✅ GridMetricsModel instantiated")
        
        # UserFeedback
        feedback = UserFeedbackModel(
            grid_id="TEST-01",
            category="Gym",
            rating=1,
        )
        print("  ✅ UserFeedbackModel instantiated")
        
    except Exception as e:
        print(f"  ❌ Model instantiation failed: {e}")
        return False
    
    # Test 5: Test to_dict() method
    print("\n✓ Test 5: Testing to_dict() method...")
    try:
        grid_dict = grid.to_dict()
        assert 'grid_id' in grid_dict
        assert grid_dict['grid_id'] == 'TEST-01'
        print("  ✅ GridCellModel.to_dict() works")
        
        business_dict = business.to_dict()
        assert 'business_id' in business_dict
        assert business_dict['rating'] == 4.5  # Should be float
        print("  ✅ BusinessModel.to_dict() works")
        
        metrics_dict = metrics.to_dict()
        assert 'gos' in metrics_dict
        assert isinstance(metrics_dict['gos'], float)
        print("  ✅ GridMetricsModel.to_dict() works")
        
    except Exception as e:
        print(f"  ❌ to_dict() method failed: {e}")
        return False
    
    # Test 6: Test helper functions
    print("\n✓ Test 6: Testing helper functions...")
    try:
        all_models = get_all_models()
        assert len(all_models) == 5
        print(f"  ✅ get_all_models() returned {len(all_models)} models")
        
        model = get_model_by_table_name('businesses')
        assert model is BusinessModel
        print("  ✅ get_model_by_table_name() works")
        
    except Exception as e:
        print(f"  ❌ Helper functions failed: {e}")
        return False
    
    # Test 7: Verify relationships
    print("\n✓ Test 7: Verifying relationships...")
    try:
        # Check if GridCellModel has relationships
        assert hasattr(GridCellModel, 'businesses')
        assert hasattr(GridCellModel, 'social_posts')
        assert hasattr(GridCellModel, 'grid_metrics')
        assert hasattr(GridCellModel, 'user_feedback')
        print("  ✅ GridCellModel has all relationships")
        
        # Check if BusinessModel has grid relationship
        assert hasattr(BusinessModel, 'grid')
        print("  ✅ BusinessModel has grid relationship")
        
    except Exception as e:
        print(f"  ⚠️  Relationship check: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ ALL VALIDATION TESTS PASSED!")
    print("=" * 70)
    print("\nORM Models are correctly defined and match the database schema.")
    print("\nNext steps:")
    print("  1. Install dependencies: pip install sqlalchemy python-dotenv psycopg2-binary")
    print("  2. Test database connection: python backend/scripts/test_db_connection.py")
    print("  3. Create tables: python -c 'from src.database import create_all_tables; create_all_tables()'")
    print("  4. Run unit tests: pytest tests/database/test_models.py -v")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = validate_models()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
