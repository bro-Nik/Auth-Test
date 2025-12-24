from typing import List, Optional, Dict, Any

from sqlalchemy import ForeignKey, String, JSON, Text, UniqueConstraint, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String)
