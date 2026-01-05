from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import TIMESTAMP, UniqueConstraint, text, ForeignKey
from src.db.base import Base
from typing import Annotated
from src.db.enums import Status
import datetime

created_at = Annotated[datetime.datetime, 
mapped_column(TIMESTAMP, nullable=False, server_default=text("TIMEZONE('utc', now())"))]

class Purchases(Base):
    __tablename__ = "purchases"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[Status] = mapped_column(nullable=False)
    created_at: Mapped[created_at]
    
    
    __table_args__ = (
        UniqueConstraint("user_id", "course_id"),
    )