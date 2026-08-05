from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import BigInteger, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class StickerPack(Base):
    __tablename__ = "sticker_packs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    short_name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    sticker_count: Mapped[int] = mapped_column(Integer, default=0)
    sticker_format: Mapped[str] = mapped_column(String(32), default="static")  # static, animated, video
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    owner: Mapped["User"] = relationship("User", back_populates="packs")

    def __repr__(self) -> str:
        return f"<StickerPack short_name='{self.short_name}' title='{self.title}' count={self.sticker_count}>"
