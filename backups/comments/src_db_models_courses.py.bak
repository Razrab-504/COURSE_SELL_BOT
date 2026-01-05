from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import TEXT, TIMESTAMP, String, text, BigInteger
from src.db.base import Base
from typing import Annotated
from src.db.enums import ContentType
import datetime


created_at = Annotated[datetime.datetime, 
mapped_column(TIMESTAMP, nullable=False, server_default=text("TIMEZONE('utc', now())"))]

class Course(Base):
    __tablename__ = "courses"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(String(250), nullable=True)
    price: Mapped[int] = mapped_column(nullable=False)
    photo_url: Mapped[str] = mapped_column(nullable=True)
    content_type: Mapped[ContentType] = mapped_column(nullable=False)
    content_data: Mapped[str] = mapped_column(TEXT, nullable=False)
    created_at: Mapped[created_at]