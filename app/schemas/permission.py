from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class RoleResponse(BaseModel):
    id: int
    code: str
    name: str

    model_config = ConfigDict(from_attributes=True)


class PermissionResponse(BaseModel):
    id: int
    code: str
    name: str
    scope: str

    model_config = ConfigDict(from_attributes=True)


class ResourceResponse(BaseModel):
    id: int
    code: str
    name: str

    model_config = ConfigDict(from_attributes=True)


class RuleBase(BaseModel):
    role_id: int
    permission_id: int
    resource_id: Optional[int] = None
    conditions: Optional[Dict[str, Any]] = None


class RuleCreate(RuleBase):
    pass


class RuleUpdate(BaseModel):
    conditions: Optional[Dict[str, Any]] = None


class RuleResponse(RuleBase):
    id: int
    role: RoleResponse
    permission: PermissionResponse
    resource: Optional[ResourceResponse] = None

    model_config = ConfigDict(from_attributes=True)
