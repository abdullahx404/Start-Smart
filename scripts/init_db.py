"""
StartSmart - Database Initialization Script
Phase 0: Initialize PostgreSQL database with schema

This script:
1. Connects to PostgreSQL database
2. Optionally drops all existing tables
3. Executes the database schema DDL from contracts/database_schema.sql
4. Verifies table creation
5. Reports initialization status

Usage:
    # Initialize fresh database (keeps existing data)
    python scripts/init_db.py

    # Drop all tables and reinitialize (DESTRUCTIVE)
    python scripts/init_db.py --drop-existing

    # Use custom schema file
    python scripts/init_db.py --schema-file path/to/schema.sql

Environment:
    Requires DATABASE_URL in .env or environment variables
    Format: postgresql://user:password@host:port/database

Author: StartSmart Development Team
Date: January 2025
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

import psycopg2
from dotenv import load_dotenv


def get_database_url() -> str:
    """
    Get database URL from environment variables.
    
    Returns:
        str: Database connection URL
        
    Raises:
        ValueError: If DATABASE_URL not found in environment
    """
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        raise ValueError(
            "DATABASE_URL not found in environment.\n"
            "Please create .env file from .env.example and set DATABASE_URL.\n"
            "Example: postgresql://startsmart:password@localhost:5432/startsmart_db"
        )
    
    return database_url


def get_database_connection(database_url: str):
    """
    Create database connection.
    
    Args:
        database_url: PostgreSQL connection URL
        
    Returns:
        psycopg2.connection: Database connection object
        
    Raises:
        psycopg2.Error: If connection fails
    """
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except psycopg2.Error as e:
        print(f"❌ Database connection failed: {e}")
        raise


def drop_all_tables(conn) -> None:
    """
    Drop all existing tables (CASCADE).
    
    WARNING: This is destructive and will delete all data!
    
    Args:
        conn: Database connection
    """
    print("\n⚠️  DROPPING ALL EXISTING TABLES...")
    
    drop_sql = """
    -- Drop tables in reverse dependency order
    DROP TABLE IF EXISTS user_feedback CASCADE;
    DROP TABLE IF EXISTS grid_metrics CASCADE;
    DROP TABLE IF EXISTS social_posts CASCADE;
    DROP TABLE IF EXISTS businesses CASCADE;
    DROP TABLE IF EXISTS grid_cells CASCADE;
    
    -- Drop PostGIS extension if needed (usually not required)
    -- DROP EXTENSION IF EXISTS postgis CASCADE;
    """
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(drop_sql)
            conn.commit()
            print("   ✓ All tables dropped successfully")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"   ❌ Failed to drop tables: {e}")
        raise


def execute_schema(conn, schema_file: Path) -> None:
    """
    Execute SQL schema file.
    
    Args:
        conn: Database connection
        schema_file: Path to SQL schema file
        
    Raises:
        FileNotFoundError: If schema file doesn't exist
        psycopg2.Error: If SQL execution fails
    """
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
    
    print(f"\n📄 Reading schema from: {schema_file}")
    schema_sql = schema_file.read_text(encoding='utf-8')
    
    print("   Schema size:", len(schema_sql), "characters")
    
    try:
        with conn.cursor() as cursor:
            # Execute entire schema as single transaction
            cursor.execute(schema_sql)
            conn.commit()
            print("   ✓ Schema executed successfully")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"   ❌ Schema execution failed: {e}")
        raise


def verify_tables(conn) -> dict:
    """
    Verify that all expected tables exist and get row counts.
    
    Args:
        conn: Database connection
        
    Returns:
        dict: Table names -> row counts
    """
    expected_tables = [
        'grid_cells',
        'businesses',
        'social_posts',
        'grid_metrics',
        'user_feedback'
    ]
    
    print("\n🔍 Verifying table creation...")
    
    table_info = {}
    
    try:
        with conn.cursor() as cursor:
            # Check each table
            for table_name in expected_tables:
                # Check existence
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    );
                """, (table_name,))
                
                exists = cursor.fetchone()[0]
                
                if exists:
                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    count = cursor.fetchone()[0]
                    table_info[table_name] = count
                    print(f"   ✓ {table_name}: {count} rows")
                else:
                    print(f"   ❌ {table_name}: NOT FOUND")
                    table_info[table_name] = None
            
            # Check PostGIS extension
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_extension WHERE extname = 'postgis'
                );
            """)
            postgis_exists = cursor.fetchone()[0]
            print(f"\n   PostGIS extension: {'✓ Enabled' if postgis_exists else '❌ Not enabled'}")
            
    except psycopg2.Error as e:
        print(f"   ❌ Verification failed: {e}")
        raise
    
    return table_info


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Initialize StartSmart database with schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize database (safe)
  python scripts/init_db.py

  # Drop all tables and reinitialize (DESTRUCTIVE)
  python scripts/init_db.py --drop-existing

  # Use custom schema file
  python scripts/init_db.py --schema-file custom_schema.sql
        """
    )
    
    parser.add_argument(
        '--drop-existing',
        action='store_true',
        help='Drop all existing tables before initialization (DESTRUCTIVE)'
    )
    
    parser.add_argument(
        '--schema-file',
        type=str,
        default='contracts/database_schema.sql',
        help='Path to SQL schema file (default: contracts/database_schema.sql)'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("StartSmart Database Initialization - Phase 0")
    print("=" * 70)
    
    # Confirm if dropping tables
    if args.drop_existing:
        print("\n⚠️  WARNING: --drop-existing flag detected!")
        print("   This will DELETE ALL EXISTING DATA.")
        response = input("\n   Type 'yes' to confirm: ")
        
        if response.lower() != 'yes':
            print("\n❌ Initialization cancelled.")
            sys.exit(0)
    
    try:
        # Get database URL
        database_url = get_database_url()
        print(f"\n🔌 Connecting to database...")
        print(f"   URL: {database_url.split('@')[1] if '@' in database_url else 'localhost'}")
        
        # Connect to database
        conn = get_database_connection(database_url)
        print("   ✓ Connected successfully")
        
        # Drop tables if requested
        if args.drop_existing:
            drop_all_tables(conn)
        
        # Execute schema
        schema_file = Path(args.schema_file)
        execute_schema(conn, schema_file)
        
        # Verify tables
        table_info = verify_tables(conn)
        
        # Check if all tables created
        all_created = all(count is not None for count in table_info.values())
        
        print("\n" + "=" * 70)
        if all_created:
            print("✅ Database initialization complete!")
        else:
            print("⚠️  Database initialization completed with warnings")
            print("   Some tables may not have been created correctly")
        print("=" * 70)
        
        # Close connection
        conn.close()
        
        # Exit with appropriate code
        sys.exit(0 if all_created else 1)
        
    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
