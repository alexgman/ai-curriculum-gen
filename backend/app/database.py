"""Database configuration and session management."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.config import settings


# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)

# Create async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


async def get_db() -> AsyncSession:
    """Dependency to get database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables and run migrations."""
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    # Run migrations for new columns
    async with async_session() as db:
        try:
            # Add new columns if they don't exist
            migrations = [
                # research_sessions table additions
                ("research_sessions", "title", "VARCHAR(200)", "'New Research'"),
                ("research_sessions", "research_plan", "JSON", "NULL"),
                ("research_sessions", "clarification_state", "JSON", "NULL"),
                ("research_sessions", "research_data", "JSON", "NULL"),
                ("research_sessions", "client_id", "VARCHAR(100)", "NULL"),
                # messages table additions
                ("messages", "thinking_steps", "JSON", "NULL"),
                ("messages", "is_streaming", "BOOLEAN", "FALSE"),
                ("messages", "extra_data", "JSON", "NULL"),
            ]
            
            for table, column, col_type, default in migrations:
                try:
                    # Check if column exists
                    check_query = text(f"""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = '{table}' AND column_name = '{column}'
                    """)
                    result = await db.execute(check_query)
                    exists = result.scalar()
                    
                    if not exists:
                        # Add the column
                        if default == "NULL":
                            alter_query = text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
                        else:
                            alter_query = text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type} DEFAULT {default}")
                        await db.execute(alter_query)
                        print(f"✅ Added column {column} to {table}")
                except Exception as e:
                    print(f"Migration warning for {table}.{column}: {e}")
            
            await db.commit()
            print("✅ Database migrations complete")
            
        except Exception as e:
            print(f"Migration error: {e}")
            await db.rollback()

