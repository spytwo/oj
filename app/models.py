from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Theme(Base):
    __tablename__ = "themes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    subthemes: Mapped[list["Subtheme"]] = relationship(
        back_populates="theme", cascade="all, delete-orphan"
    )


class Subtheme(Base):
    __tablename__ = "subthemes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    theme_id: Mapped[int] = mapped_column(ForeignKey("themes.id", ondelete="CASCADE"))

    theme: Mapped["Theme"] = relationship(back_populates="subthemes")
    records: Mapped[list["Record"]] = relationship(
        back_populates="subtheme", cascade="all, delete-orphan"
    )


class Record(Base):
    __tablename__ = "records"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    subtheme_id: Mapped[int] = mapped_column(
        ForeignKey("subthemes.id", ondelete="CASCADE")
    )

    subtheme: Mapped["Subtheme"] = relationship(back_populates="records")
