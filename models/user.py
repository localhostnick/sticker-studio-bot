from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import BigInteger, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)  # Telegram User ID
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )
    last_active: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    packs: Mapped[List["StickerPack"]] = relationship("StickerPack", back_populates="owner", cascade="all, delete-orphan")
    history: Mapped[List["History"]] = relationship("History", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} username='{self.username}'>"
