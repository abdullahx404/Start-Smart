# Database Connection Module

## Overview

The `src/database/connection.py` module provides a robust, production-ready database connection layer using SQLAlchemy 2.0. It handles:

- ✅ PostgreSQL connection pooling
- ✅ SQLite support for testing
- ✅ Automatic session lifecycle management
- ✅ Thread-safe operations
- ✅ Connection health checks
- ✅ Proper error handling and logging

## Quick Start

### 1. Install Dependencies

```powershell
pip install sqlalchemy python-dotenv psycopg2-binary
```

### 2. Configure Environment

Create/update `.env` file in project root:

```env
DATABASE_URL=postgresql://postgres:12113@localhost:5432/startsmart_dev
SKIP_DB_CHECK=false  # Set to true to skip connection check on import
```

### 3. Test Connection

```powershell
python backend/scripts/test_db_connection.py
```

Expected output:
```
✅ ALL TESTS PASSED!
Your database connection is ready for Phase 1 development.
```

## Usage Examples

### Context Manager Pattern (Recommended)

```python
from src.database import get_session
from src.database.models import BusinessModel

# Query example
with get_session() as session:
    businesses = session.query(BusinessModel).filter_by(category="Gym").all()
    for business in businesses:
        print(f"{business.name} - Rating: {business.rating}")

# Session automatically commits and closes
```

### Insert Data

```python
from src.database import get_session
from src.database.models import BusinessModel

with get_session() as session:
    new_business = BusinessModel(
        business_id="gym-001",
        name="PowerHouse Gym",
        lat=24.8300,
        lon=67.0600,
        category="Gym",
        rating=4.5,
        review_count=120
    )
    session.add(new_business)
    # Auto-commits on successful exit
```

### Bulk Insert

```python
from src.database import get_session
from src.database.models import BusinessModel

businesses = [
    BusinessModel(business_id=f"gym-{i}", name=f"Gym {i}", ...)
    for i in range(100)
]

with get_session() as session:
    session.bulk_save_objects(businesses)
    # Efficient bulk insert
```

### Update Data

```python
from src.database import get_session
from src.database.models import BusinessModel

with get_session() as session:
    business = session.query(BusinessModel).filter_by(
        business_id="gym-001"
    ).first()
    
    if business:
        business.rating = 4.8
        business.review_count = 150
        # Auto-commits on exit
```

### Delete Data

```python
from src.database import get_session
from src.database.models import BusinessModel

with get_session() as session:
    session.query(BusinessModel).filter_by(
        business_id="gym-001"
    ).delete()
    # Auto-commits on exit
```

### Error Handling

```python
from src.database import get_session
from sqlalchemy.exc import IntegrityError

try:
    with get_session() as session:
        # Your database operations
        pass
except IntegrityError as e:
    print(f"Constraint violation: {e}")
except Exception as e:
    print(f"Database error: {e}")
```

## Advanced Usage

### Direct Session (Manual Cleanup)

```python
from src.database import get_session_direct

session = get_session_direct()
try:
    result = session.query(BusinessModel).all()
    session.commit()
except Exception as e:
    session.rollback()
    raise
finally:
    session.close()  # MUST close manually!
```

### Create Tables (Testing Only)

```python
from src.database import create_all_tables

# Import all models first
from src.database.models import (
    GridCellModel,
    BusinessModel,
    SocialPostModel,
    GridMetricsModel,
    UserFeedbackModel,
)

# Create all tables
create_all_tables()
```

### Health Check

```python
from src.database import check_connection

if check_connection():
    print("Database is accessible")
else:
    print("Database connection failed")
```

## Configuration Details

### Connection Pooling (PostgreSQL)

```python
# Default settings in connection.py
pool_size=5          # Keep 5 connections open
max_overflow=10      # Allow up to 15 total connections (5 + 10)
pool_timeout=30      # Wait 30 seconds for available connection
pool_recycle=3600    # Recycle connections after 1 hour
pool_pre_ping=True   # Test connections before use
```

### SQLite Configuration

```python
# SQLite uses NullPool (no connection pooling)
poolclass=NullPool
connect_args={"check_same_thread": False}  # Allow multi-threading
```

## Important Notes

### Thread Safety

- ✅ **Session per request**: Always create a new session for each operation
- ✅ **Context manager**: Use `with get_session()` for automatic cleanup
- ❌ **Never share sessions**: Each thread/request needs its own session

### Transaction Management

```python
# Auto-commit on success
with get_session() as session:
    session.add(new_object)
    # Commits automatically if no exceptions

# Auto-rollback on error
with get_session() as session:
    session.add(new_object)
    raise Exception("Something failed")
    # Automatically rolls back
```

### Performance Tips

1. **Use bulk operations** for inserting many records:
   ```python
   session.bulk_save_objects(large_list)
   ```

2. **Enable query logging** during development:
   ```python
   # In connection.py, change:
   "echo": True  # Logs all SQL queries
   ```

3. **Use connection pooling** (PostgreSQL only):
   - Pre-configured in connection.py
   - Reuses connections for better performance

4. **Close sessions promptly**:
   - Always use context manager
   - Avoid long-running transactions

## Troubleshooting

### Connection Errors

**Problem**: `DATABASE_URL environment variable not set`

**Solution**:
```powershell
# Create .env file with:
DATABASE_URL=postgresql://postgres:12113@localhost:5432/startsmart_dev
```

---

**Problem**: `sqlalchemy` module not found

**Solution**:
```powershell
pip install sqlalchemy python-dotenv psycopg2-binary
```

---

**Problem**: Connection timeout

**Solution**:
1. Check PostgreSQL is running: `Get-Service postgresql*`
2. Test connection: `psql -U postgres -d startsmart_dev`
3. Check firewall settings

---

**Problem**: Pool size exceeded

**Solution**:
```python
# Increase pool settings in connection.py
pool_size=10
max_overflow=20
```

## Testing

### Unit Tests

```powershell
pytest tests/database/test_connection.py -v
```

### Integration Tests

```powershell
# Requires running PostgreSQL
pytest tests/database/ -v --cov=src/database
```

## File Structure

```
backend/
├── src/
│   └── database/
│       ├── __init__.py              # Exports: get_session, engine, Base
│       ├── connection.py            # ✅ CREATED - SQLAlchemy setup
│       └── models.py                # ⏳ TODO - ORM models
├── tests/
│   └── database/
│       ├── __init__.py
│       └── test_connection.py       # ✅ CREATED - Unit tests
└── scripts/
    └── test_db_connection.py        # ✅ CREATED - Quick test
```

## Next Steps

1. ✅ Database connection setup complete
2. ⏳ Create ORM models in `src/database/models.py`
3. ⏳ Implement adapters in `src/adapters/`
4. ⏳ Create data fetching scripts

## References

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [PHASE_LOG.md](../../PHASE_LOG.md) - Phase 0 deliverables
- [contracts/database_schema.sql](../../contracts/database_schema.sql) - Database schema
