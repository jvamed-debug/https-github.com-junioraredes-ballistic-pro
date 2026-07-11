"""RBAC — Role-Based Access Control para a plataforma."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Permission(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    ADMIN = "admin"
    MANAGE_USERS = "manage_users"
    MANAGE_AGENTS = "manage_agents"
    MANAGE_WORKFLOWS = "manage_workflows"
    VIEW_AUDIT = "view_audit"
    MANAGE_TENANTS = "manage_tenants"


class SystemRole(str, Enum):
    VIEWER = "viewer"
    DEVELOPER = "developer"
    LEAD = "lead"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


ROLE_PERMISSIONS: dict[SystemRole, set[Permission]] = {
    SystemRole.VIEWER: {Permission.READ},
    SystemRole.DEVELOPER: {Permission.READ, Permission.WRITE, Permission.EXECUTE},
    SystemRole.LEAD: {
        Permission.READ, Permission.WRITE, Permission.EXECUTE,
        Permission.DELETE, Permission.MANAGE_AGENTS, Permission.MANAGE_WORKFLOWS,
    },
    SystemRole.ADMIN: {
        Permission.READ, Permission.WRITE, Permission.EXECUTE, Permission.DELETE,
        Permission.ADMIN, Permission.MANAGE_USERS, Permission.MANAGE_AGENTS,
        Permission.MANAGE_WORKFLOWS, Permission.VIEW_AUDIT,
    },
    SystemRole.SUPER_ADMIN: {p for p in Permission},
}


@dataclass
class User:
    id: str
    username: str
    email: str
    role: SystemRole = SystemRole.VIEWER
    tenant_id: str = ""
    active: bool = True
    custom_permissions: set[Permission] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)


class RBACManager:
    """Gerencia usuários, papéis e permissões."""

    def __init__(self) -> None:
        self._users: dict[str, User] = {}
        self._counter = 0
        self._resource_policies: dict[str, set[Permission]] = {}

    def create_user(self, username: str, email: str, role: SystemRole = SystemRole.VIEWER,
                    tenant_id: str = "") -> User:
        self._counter += 1
        user = User(
            id=f"USR-{self._counter:06d}",
            username=username,
            email=email,
            role=role,
            tenant_id=tenant_id,
        )
        self._users[user.id] = user
        return user

    def get_user(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    def get_by_username(self, username: str) -> User | None:
        for u in self._users.values():
            if u.username == username:
                return u
        return None

    def update_role(self, user_id: str, role: SystemRole) -> User | None:
        user = self._users.get(user_id)
        if user:
            user.role = role
        return user

    def grant_permission(self, user_id: str, permission: Permission) -> bool:
        user = self._users.get(user_id)
        if user:
            user.custom_permissions.add(permission)
            return True
        return False

    def revoke_permission(self, user_id: str, permission: Permission) -> bool:
        user = self._users.get(user_id)
        if user:
            user.custom_permissions.discard(permission)
            return True
        return False

    def has_permission(self, user_id: str, permission: Permission) -> bool:
        user = self._users.get(user_id)
        if not user or not user.active:
            return False
        role_perms = ROLE_PERMISSIONS.get(user.role, set())
        return permission in role_perms or permission in user.custom_permissions

    def check_access(self, user_id: str, resource: str, action: Permission) -> bool:
        if not self.has_permission(user_id, action):
            return False
        resource_required = self._resource_policies.get(resource)
        if resource_required and action not in resource_required:
            return False
        return True

    def set_resource_policy(self, resource: str, required_permissions: set[Permission]) -> None:
        self._resource_policies[resource] = required_permissions

    def get_user_permissions(self, user_id: str) -> set[Permission]:
        user = self._users.get(user_id)
        if not user:
            return set()
        role_perms = ROLE_PERMISSIONS.get(user.role, set())
        return role_perms | user.custom_permissions

    def deactivate_user(self, user_id: str) -> bool:
        user = self._users.get(user_id)
        if user:
            user.active = False
            return True
        return False

    def list_users(self, tenant_id: str | None = None, role: SystemRole | None = None) -> list[User]:
        users = list(self._users.values())
        if tenant_id:
            users = [u for u in users if u.tenant_id == tenant_id]
        if role:
            users = [u for u in users if u.role == role]
        return users

    @property
    def user_count(self) -> int:
        return len(self._users)
