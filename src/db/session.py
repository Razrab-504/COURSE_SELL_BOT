from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.db.config import settings

engine = create_async_engine(url=settings.DATABASE_URL, echo=True,)
LocalSession = async_sessionmaker(autoflush=False, autocommit=False, bind=engine)