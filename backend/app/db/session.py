from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings

# 1. Create the Engine
# The engine manages the connection pool to the database.
# We use create_async_engine because we want our server to be able to handle 
# thousands of requests simultaneously without waiting for the database to respond.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False, # Set to True to see all SQL queries printed in the terminal
    future=True
)

# 2. Create the Session Factory
# A session is a single "conversation" with the database.
# async_sessionmaker generates new sessions for us when we need them.
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False # Prevents SQLAlchemy from wiping our variables after saving to DB
)

# 3. Dependency Injection Function
# We will use this function in FastAPI routes to get a database connection.
# The 'yield' keyword makes this a generator. It opens the connection, gives it to the route,
# and then automatically closes it when the route is finished.
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session