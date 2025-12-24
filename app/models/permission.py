from typing import List, Optional, Dict, Any

from sqlalchemy import ForeignKey, String, JSON, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# Таблица связей для роль-разрешение-ресурс
class RolePermissionResource(Base):
    __tablename__ = "role_permission_resources"

    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"))
    resource_id: Mapped[Optional[int]] = mapped_column(ForeignKey("resources.id"), nullable=True)

    # Условия доступа (например, фильтрация по определенным полям)
    # Пример: {"min_price": 100, "status": ["active", "pending"]}
    conditions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=None)

    # Relationships
    role: Mapped["Role"] = relationship(back_populates="permission_resources")
    permission: Mapped["Permission"] = relationship(back_populates="role_resources")
    resource: Mapped[Optional["Resource"]] = relationship(back_populates="role_permissions")


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String, unique=True)
    name: Mapped[str] = mapped_column(String)

    # Relationships
    users: Mapped[List["User"]] = relationship(back_populates="role")
    permission_resources: Mapped[List["RolePermissionResource"]] = relationship(
        back_populates="role",
        cascade="all, delete-orphan"
    )


class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint('code', 'scope', name='uq_permission_code_scope'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    scope: Mapped[str] = mapped_column(String(50))  # all, own

    # Relationships
    role_resources: Mapped[List["RolePermissionResource"]] = relationship(
        back_populates="permission",
        cascade="all, delete-orphan"
    )


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String, unique=True)
    name: Mapped[str] = mapped_column(String)

    # Relationships
    role_permissions: Mapped[List["RolePermissionResource"]] = relationship(
        back_populates="resource",
        cascade="all, delete-orphan"
    )
