from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio.engine import create_async_engine
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.settings import s

DATABASE_URL = URL.create(
    "postgresql+asyncpg",
    username=s.postgres_user,
    password=s.postgres_password,
    host=s.postgres_host,
    database=s.postgres_db,
)

engine = create_async_engine(DATABASE_URL, echo=True)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session_maker() as session:
        yield session
