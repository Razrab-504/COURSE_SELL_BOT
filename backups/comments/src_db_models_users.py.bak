from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import TIMESTAMP, String, text, BigInteger, Boolean
from src.db.base import Base
from typing import Annotated
import datetime

created_at = Annotated[datetime.datetime, 
mapped_column(TIMESTAMP, nullable=False, server_default=text("TIMEZONE('utc', now())"))]

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(30), nullable=True)
    last_name: Mapped[str] = mapped_column(String(30), nullable=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    created_at: Mapped[created_at]