"""Tests for Release 0.9 — Enterprise (multi-tenant, audit, RBAC)."""

from __future__ import annotations

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.enterprise.tenant import TenantManager, TenantPlan, TenantStatus, PLAN_LIMITS
from core.enterprise.audit import AuditLog, AuditAction, AuditSeverity
from core.enterprise.rbac import RBACManager, SystemRole, Permission, ROLE_PERMISSIONS


class TestTenantManager(unittest.TestCase):
    def test_create_tenant(self) -> None:
        mgr = TenantManager()
        tenant = mgr.create("Acme Corp", "acme", owner_email="admin@acme.com")
        assert tenant.id == "TNT-000001"
        assert tenant.name == "Acme Corp"
        assert tenant.status == TenantStatus.ACTIVE

    def test_get_by_slug(self) -> None:
        mgr = TenantManager()
        mgr.create("Acme", "acme")
        tenant = mgr.get_by_slug("acme")
        assert tenant is not None
        assert tenant.name == "Acme"

    def test_update_plan(self) -> None:
        mgr = TenantManager()
        tenant = mgr.create("Test", "test")
        mgr.update_plan(tenant.id, TenantPlan.PROFESSIONAL)
        updated = mgr.get(tenant.id)
        assert updated is not None
        assert updated.plan == TenantPlan.PROFESSIONAL

    def test_suspend_and_activate(self) -> None:
        mgr = TenantManager()
        tenant = mgr.create("Test", "test")
        mgr.suspend(tenant.id)
        assert mgr.get(tenant.id).status == TenantStatus.SUSPENDED
        mgr.activate(tenant.id)
        assert mgr.get(tenant.id).status == TenantStatus.ACTIVE

    def test_check_limit(self) -> None:
        mgr = TenantManager()
        tenant = mgr.create("Test", "test", plan=TenantPlan.FREE)
        assert mgr.check_limit(tenant.id, "projects", 2) is True
        assert mgr.check_limit(tenant.id, "projects", 5) is False

    def test_enterprise_unlimited(self) -> None:
        mgr = TenantManager()
        tenant = mgr.create("Big Co", "bigco", plan=TenantPlan.ENTERPRISE)
        assert mgr.check_limit(tenant.id, "projects", 999) is True

    def test_list_tenants(self) -> None:
        mgr = TenantManager()
        mgr.create("A", "a")
        mgr.create("B", "b")
        assert mgr.count == 2
        assert len(mgr.list_tenants()) == 2

    def test_plan_limits_defined(self) -> None:
        for plan in TenantPlan:
            assert plan in PLAN_LIMITS


class TestAuditLog(unittest.TestCase):
    def test_record_entry(self) -> None:
        log = AuditLog()
        entry = log.record(
            actor="user1", action=AuditAction.CREATE,
            resource_type="project", resource_id="PRJ-001",
        )
        assert entry.id == "AUD-00000001"
        assert log.total_entries == 1

    def test_query_by_actor(self) -> None:
        log = AuditLog()
        log.record("user1", AuditAction.CREATE, "project", "P1")
        log.record("user2", AuditAction.READ, "project", "P1")
        log.record("user1", AuditAction.UPDATE, "project", "P1")
        results = log.query(actor="user1")
        assert len(results) == 2

    def test_query_by_action(self) -> None:
        log = AuditLog()
        log.record("u1", AuditAction.CREATE, "p", "1")
        log.record("u1", AuditAction.DELETE, "p", "2")
        results = log.query(action=AuditAction.DELETE)
        assert len(results) == 1

    def test_failed_actions(self) -> None:
        log = AuditLog()
        log.record("u1", AuditAction.LOGIN, "auth", "session", success=False)
        log.record("u1", AuditAction.LOGIN, "auth", "session", success=True)
        failed = log.failed_actions()
        assert len(failed) == 1

    def test_security_events(self) -> None:
        log = AuditLog()
        log.record("u1", AuditAction.DELETE, "db", "prod",
                   severity=AuditSeverity.CRITICAL)
        log.record("u1", AuditAction.READ, "file", "config",
                   severity=AuditSeverity.LOW)
        events = log.security_events()
        assert len(events) == 1

    def test_count_by_action(self) -> None:
        log = AuditLog()
        log.record("u1", AuditAction.READ, "a", "1")
        log.record("u1", AuditAction.READ, "b", "2")
        log.record("u1", AuditAction.CREATE, "c", "3")
        assert log.count_by_action(AuditAction.READ) == 2

    def test_get_entry(self) -> None:
        log = AuditLog()
        entry = log.record("u1", AuditAction.CREATE, "project", "P1")
        found = log.get_entry(entry.id)
        assert found is not None
        assert found.actor == "u1"

    def test_query_by_tenant(self) -> None:
        log = AuditLog()
        log.record("u1", AuditAction.CREATE, "p", "1", tenant_id="T1")
        log.record("u2", AuditAction.CREATE, "p", "2", tenant_id="T2")
        results = log.query(tenant_id="T1")
        assert len(results) == 1


class TestRBACManager(unittest.TestCase):
    def test_create_user(self) -> None:
        mgr = RBACManager()
        user = mgr.create_user("alice", "alice@test.com", SystemRole.DEVELOPER)
        assert user.id == "USR-000001"
        assert user.role == SystemRole.DEVELOPER

    def test_has_permission(self) -> None:
        mgr = RBACManager()
        user = mgr.create_user("alice", "a@t.com", SystemRole.DEVELOPER)
        assert mgr.has_permission(user.id, Permission.READ) is True
        assert mgr.has_permission(user.id, Permission.WRITE) is True
        assert mgr.has_permission(user.id, Permission.ADMIN) is False

    def test_viewer_limited(self) -> None:
        mgr = RBACManager()
        user = mgr.create_user("bob", "b@t.com", SystemRole.VIEWER)
        assert mgr.has_permission(user.id, Permission.READ) is True
        assert mgr.has_permission(user.id, Permission.WRITE) is False

    def test_admin_permissions(self) -> None:
        mgr = RBACManager()
        user = mgr.create_user("admin", "a@t.com", SystemRole.ADMIN)
        assert mgr.has_permission(user.id, Permission.ADMIN) is True
        assert mgr.has_permission(user.id, Permission.MANAGE_USERS) is True
        assert mgr.has_permission(user.id, Permission.MANAGE_TENANTS) is False

    def test_super_admin_all(self) -> None:
        mgr = RBACManager()
        user = mgr.create_user("root", "r@t.com", SystemRole.SUPER_ADMIN)
        for perm in Permission:
            assert mgr.has_permission(user.id, perm) is True

    def test_grant_custom_permission(self) -> None:
        mgr = RBACManager()
        user = mgr.create_user("alice", "a@t.com", SystemRole.VIEWER)
        assert mgr.has_permission(user.id, Permission.EXECUTE) is False
        mgr.grant_permission(user.id, Permission.EXECUTE)
        assert mgr.has_permission(user.id, Permission.EXECUTE) is True

    def test_revoke_custom_permission(self) -> None:
        mgr = RBACManager()
        user = mgr.create_user("alice", "a@t.com", SystemRole.VIEWER)
        mgr.grant_permission(user.id, Permission.WRITE)
        mgr.revoke_permission(user.id, Permission.WRITE)
        assert mgr.has_permission(user.id, Permission.WRITE) is False

    def test_update_role(self) -> None:
        mgr = RBACManager()
        user = mgr.create_user("alice", "a@t.com", SystemRole.VIEWER)
        mgr.update_role(user.id, SystemRole.LEAD)
        assert mgr.has_permission(user.id, Permission.DELETE) is True

    def test_deactivate_user(self) -> None:
        mgr = RBACManager()
        user = mgr.create_user("alice", "a@t.com", SystemRole.ADMIN)
        mgr.deactivate_user(user.id)
        assert mgr.has_permission(user.id, Permission.READ) is False

    def test_get_by_username(self) -> None:
        mgr = RBACManager()
        mgr.create_user("alice", "a@t.com")
        user = mgr.get_by_username("alice")
        assert user is not None

    def test_list_users_by_tenant(self) -> None:
        mgr = RBACManager()
        mgr.create_user("alice", "a@t.com", tenant_id="T1")
        mgr.create_user("bob", "b@t.com", tenant_id="T2")
        users = mgr.list_users(tenant_id="T1")
        assert len(users) == 1

    def test_check_access_with_resource_policy(self) -> None:
        mgr = RBACManager()
        user = mgr.create_user("alice", "a@t.com", SystemRole.DEVELOPER)
        mgr.set_resource_policy("production_db", {Permission.ADMIN})
        assert mgr.check_access(user.id, "production_db", Permission.WRITE) is False

    def test_role_permissions_complete(self) -> None:
        for role in SystemRole:
            assert role in ROLE_PERMISSIONS


if __name__ == "__main__":
    unittest.main()
