"""Tests for core.auth module."""

import pytest
from unittest.mock import patch, MagicMock
from core.auth import authenticate, register_user, recover_password


class TestAuthenticate:
    @patch("core.auth.log_action")
    @patch("core.auth.managed_session")
    def test_valid_credentials(self, mock_session_ctx, mock_log):
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.check_password.return_value = True

        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        mock_session_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = authenticate("testuser", "password123")
        assert result is mock_user
        mock_log.assert_called_once_with(1, "auth_login_success", "users", 1)

    @patch("core.auth.log_action")
    @patch("core.auth.managed_session")
    def test_wrong_password(self, mock_session_ctx, mock_log):
        mock_user = MagicMock()
        mock_user.id = 2
        mock_user.check_password.return_value = False

        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        mock_session_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = authenticate("testuser", "wrong")
        assert result is None
        mock_log.assert_called_once_with(2, "auth_login_failed", "users", 2, new={"info": "Senha incorreta"})

    @patch("core.auth.log_action")
    @patch("core.auth.managed_session")
    def test_nonexistent_user(self, mock_session_ctx, mock_log):
        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_session_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = authenticate("nobody", "password123")
        assert result is None
        mock_log.assert_not_called()


class TestRegisterUser:
    def test_invalid_username_rejected(self):
        ok, msg = register_user("ab", "password123", None, None, None, None)
        assert ok is False
        assert msg  # validation error message

    def test_invalid_password_rejected(self):
        ok, msg = register_user("validuser", "short", None, None, None, None)
        assert ok is False
        assert msg

    def test_invalid_cpf_rejected(self):
        ok, msg = register_user("validuser", "password123", "Name", "123", None, None)
        assert ok is False
        assert msg

    @patch("core.auth.log_action")
    @patch("core.auth.managed_session")
    def test_duplicate_user_rejected(self, mock_session_ctx, mock_log):
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = MagicMock()
        mock_session_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_ctx.return_value.__exit__ = MagicMock(return_value=False)

        ok, msg = register_user("validuser", "password123", None, None, None, None)
        assert ok is False
        assert "em uso" in msg.lower() or "inválidos" in msg.lower()

    @patch("core.auth.log_action")
    @patch("core.auth.managed_session")
    def test_successful_registration(self, mock_session_ctx, mock_log):
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        mock_new_user = MagicMock()
        mock_new_user.id = 42

        def capture_add(user):
            user.id = 42

        mock_session.add.side_effect = capture_add
        mock_session_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_ctx.return_value.__exit__ = MagicMock(return_value=False)

        ok, msg = register_user("validuser", "password123", "Test User", None, None, None)
        assert ok is True
        assert "sucesso" in msg.lower()
        mock_session.add.assert_called_once()


class TestRecoverPassword:
    @patch("core.auth.log_action")
    @patch("core.auth.managed_session")
    def test_always_returns_generic_message(self, mock_session_ctx, mock_log):
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_ctx.return_value.__exit__ = MagicMock(return_value=False)

        ok, msg = recover_password("nobody@test.com")
        assert ok is True
        assert "instruções" in msg.lower() or "instrucoes" in msg.lower() or "recuperação" in msg.lower()

    @patch("core.auth.log_action")
    @patch("core.auth.managed_session")
    def test_existing_user_logs_action(self, mock_session_ctx, mock_log):
        mock_user = MagicMock()
        mock_user.id = 5

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_user
        mock_session_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_ctx.return_value.__exit__ = MagicMock(return_value=False)

        ok, msg = recover_password("user@test.com")
        assert ok is True
        mock_log.assert_called_once_with(5, "auth_recovery_requested", "users", 5)
