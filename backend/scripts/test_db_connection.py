"""
Database Connection Quick Test

Run this script to verify your database connection is working.

Usage:
    python backend/scripts/test_db_connection.py
"""

import sys
import os

# Add parent directory to path so we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def main():
    print("=" * 60)
    print("StartSmart Database Connection Test")
    print("=" * 60)
    
    # Check if DATABASE_URL is set
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("\n❌ ERROR: DATABASE_URL environment variable not set!")
        print("\nPlease set it in your .env file:")
        print("  DATABASE_URL=postgresql://user:password@localhost:5432/startsmart_dev")
        sys.exit(1)
    
    print(f"\n📊 Database URL: {database_url.split('@')[-1] if '@' in database_url else 'sqlite'}")
    
    # Try to import connection module
    print("\n⏳ Importing database connection module...")
    try:
        from src.database import (
            get_session, 
            engine, 
            check_connection,
            create_all_tables,
        )
        print("✅ Connection module imported successfully")
    except ImportError as e:
        print(f"\n❌ ERROR: Failed to import database module!")
        print(f"   {e}")
        print("\nMake sure you have installed dependencies:")
        print("   pip install sqlalchemy python-dotenv psycopg2-binary")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)
    
    # Test connection
    print("\n⏳ Testing database connection...")
    if check_connection():
        print("✅ Database connection successful!")
    else:
        print("❌ Database connection failed!")
        print("\nPlease check:")
        print("  1. PostgreSQL is running")
        print("  2. Database exists (startsmart_dev)")
        print("  3. Credentials are correct")
        print("  4. Firewall allows connection")
        sys.exit(1)
    
    # Test session creation
    print("\n⏳ Testing session creation...")
    try:
        with get_session() as session:
            # Execute simple query
            result = session.execute("SELECT 1 as test").fetchone()
            if result and result[0] == 1:
                print("✅ Session creation successful!")
            else:
                print("❌ Session query returned unexpected result")
                sys.exit(1)
    except Exception as e:
        print(f"❌ Session creation failed: {e}")
        sys.exit(1)
    
    # Display engine configuration
    print("\n📋 Engine Configuration:")
    print(f"   Dialect: {engine.dialect.name}")
    print(f"   Driver: {engine.driver}")
    print(f"   Pool Size: {engine.pool.size() if hasattr(engine.pool, 'size') else 'N/A'}")
    
    # Success summary
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nYour database connection is ready for Phase 1 development.")
    print("\nNext steps:")
    print("  1. Create ORM models in src/database/models.py")
    print("  2. Implement adapters in src/adapters/")
    print("  3. Run: python scripts/fetch_google_places.py")
    print()


if __name__ == "__main__":
    main()
