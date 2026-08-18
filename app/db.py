from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings
from app.logger import get_logger

logger = get_logger(__name__)

# SQLAlchemy base class for models
Base = declarative_base()

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ECHO_SQL,
    future=True,
    pool_pre_ping=True,
)

# Session factory — importable directly (as `async_session`) by services that
# need short-lived sessions opened AFTER a slow external call (e.g. Groq),
# rather than a request-scoped session held open for the whole request.
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    future=True,
)


async def get_db_session() -> AsyncSession:
    """Request-scoped session for FastAPI's Depends().

    Use this ONLY for routes that do pure DB reads/writes with no slow
    external call (Groq, etc.) in between — e.g. GET /cases/{id},
    GET /users/{id}/cases. For /cases/generate and /solutions/evaluate,
    services open their own short-lived session via `async_session`
    directly, so the connection isn't held open during the Groq call.
    """
    async with async_session() as session:
        yield session


async def init_db():
    """Initialize database tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise