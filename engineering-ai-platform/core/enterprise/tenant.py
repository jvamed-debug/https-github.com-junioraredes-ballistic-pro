"""Multi-Tenant — isolamento e gerenciamento de tenants."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    DEACTIVATED = "deactivated"


class TenantPlan(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


@dataclass
class TenantLimits:
    max_projects: int = 3
    max_agents: int = 4
    max_users: int = 5
    max_requests_per_hour: int = 100
    max_storage_mb: int = 500
    features: list[str] = field(default_factory=list)


PLAN_LIMITS: dict[TenantPlan, TenantLimits] = {
    TenantPlan.FREE: TenantLimits(
        max_projects=3, max_agents=4, max_users=5,
        max_requests_per_hour=100, max_storage_mb=500,
        features=["basic_agents", "basic_workflows"],
    ),
    TenantPlan.STARTER: TenantLimits(
        max_projects=10, max_agents=6, max_users=20,
        max_requests_per_hour=500, max_storage_mb=5000,
        features=["basic_agents", "basic_workflows", "knowledge_base", "api_access"],
    ),
    TenantPlan.PROFESSIONAL: TenantLimits(
        max_projects=50, max_agents=8, max_users=100,
        max_requests_per_hour=2000, max_storage_mb=50000,
        features=["all_agents", "workflows", "knowledge_base", "api_access", "custom_providers"],
    ),
    TenantPlan.ENTERPRISE: TenantLimits(
        max_projects=0, max_agents=8, max_users=0,
        max_requests_per_hour=0, max_storage_mb=0,
        features=["all_agents", "workflows", "knowledge_base", "api_access",
                  "custom_providers", "audit_log", "rbac", "sso", "custom_integrations"],
    ),
}


@dataclass
class Tenant:
    id: str
    name: str
    slug: str
    plan: TenantPlan = TenantPlan.FREE
    status: TenantStatus = TenantStatus.ACTIVE
    owner_email: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


class TenantManager:
    """Gerencia tenants, planos e limites."""

    def __init__(self) -> None:
        self._tenants: dict[str, Tenant] = {}
        self._counter = 0

    def create(self, name: str, slug: str, plan: TenantPlan = TenantPlan.FREE,
               owner_email: str = "") -> Tenant:
        self._counter += 1
        tenant = Tenant(
            id=f"TNT-{self._counter:06d}",
            name=name,
            slug=slug,
            plan=plan,
            owner_email=owner_email,
        )
        self._tenants[tenant.id] = tenant
        return tenant

    def get(self, tenant_id: str) -> Tenant | None:
        return self._tenants.get(tenant_id)

    def get_by_slug(self, slug: str) -> Tenant | None:
        for t in self._tenants.values():
            if t.slug == slug:
                return t
        return None

    def update_plan(self, tenant_id: str, plan: TenantPlan) -> Tenant | None:
        tenant = self._tenants.get(tenant_id)
        if tenant:
            tenant.plan = plan
        return tenant

    def suspend(self, tenant_id: str) -> bool:
        tenant = self._tenants.get(tenant_id)
        if tenant:
            tenant.status = TenantStatus.SUSPENDED
            return True
        return False

    def activate(self, tenant_id: str) -> bool:
        tenant = self._tenants.get(tenant_id)
        if tenant:
            tenant.status = TenantStatus.ACTIVE
            return True
        return False

    def get_limits(self, tenant_id: str) -> TenantLimits:
        tenant = self._tenants.get(tenant_id)
        if tenant:
            return PLAN_LIMITS.get(tenant.plan, PLAN_LIMITS[TenantPlan.FREE])
        return PLAN_LIMITS[TenantPlan.FREE]

    def check_limit(self, tenant_id: str, resource: str, current_count: int) -> bool:
        limits = self.get_limits(tenant_id)
        max_val = getattr(limits, f"max_{resource}", 0)
        if max_val == 0:
            return True
        return current_count < max_val

    def list_tenants(self, status: TenantStatus | None = None) -> list[Tenant]:
        tenants = list(self._tenants.values())
        if status:
            tenants = [t for t in tenants if t.status == status]
        return tenants

    @property
    def count(self) -> int:
        return len(self._tenants)
