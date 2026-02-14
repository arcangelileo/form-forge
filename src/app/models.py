import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    plan: Mapped[str] = mapped_column(String(20), default="free", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    forms: Mapped[list["Form"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class Form(Base):
    __tablename__ = "forms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    allowed_origins: Mapped[str] = mapped_column(String(500), default="*", nullable=False)
    redirect_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notification_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="forms")
    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="form", cascade="all, delete-orphan"
    )


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    form_id: Mapped[int] = mapped_column(Integer, ForeignKey("forms.id"), nullable=False)
    data: Mapped[str] = mapped_column(Text, nullable=False)  # JSON blob
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    is_spam: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    form: Mapped["Form"] = relationship(back_populates="submissions")
