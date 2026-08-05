from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import BigInteger, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class History(Base):
    __tablename__ = "history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    operation_type: Mapped[str] = mapped_column(String(64), nullable=False)  # CREATE, CLONE, DOWNLOAD, RENAME, DELETE, ADD
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="SUCCESS")  # SUCCESS, FAILED, CANCELLED
    
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship("User", back_populates="history")

    def __repr__(self) -> str:
        return f"<History id={self.id} user_id={self.user_id} op='{self.operation_type}' status='{self.status}'>"
