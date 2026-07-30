"""Tests for core.models module — encryption, password hashing, sessions, audit logging."""

import pytest
import base64
import os
from unittest.mock import patch, MagicMock

from cryptography.fernet import Fernet


class TestGetEncryptionSuite:
    @patch("core.models.st")
    def test_fernet_key_env_var(self, mock_st):
        from cryptography.fernet import Fernet
        key = Fernet.generate_key().decode()
        with patch.dict(os.environ, {"FERNET_KEY": key}, clear=False):
            from core.models import get_encryption_suite
            suite = get_encryption_suite()
            assert suite is not None
            plaintext = b"test data"
            assert suite.decrypt(suite.encrypt(plaintext)) == plaintext

    @patch("core.models.st")
    def test_invalid_fernet_key_in_production_raises(self, mock_st):
        """An invalid FERNET_KEY in production should raise RuntimeError."""
        mock_secrets = MagicMock()
        mock_secrets.__contains__ = MagicMock(return_value=False)
        mock_secrets.__getitem__ = MagicMock(side_effect=KeyError)
        mock_secrets.get = MagicMock(return_value=None)
        mock_st.secrets = mock_secrets
        with patch.dict(os.environ, {"FERNET_KEY": "not-a-valid-key", "DATABASE_URL": ""}, clear=False):
            from core.models import get_encryption_suite
            with pytest.raises(RuntimeError, match="CRITICAL SECURITY"):
                get_encryption_suite()

    @patch("core.models.st")
    def test_dev_mode_returns_none_with_warning(self, mock_st):
        mock_st.secrets.__contains__ = MagicMock(return_value=False)
        mock_st.secrets.__getitem__ = MagicMock(side_effect=KeyError)
        mock_st.secrets.get = MagicMock(return_value=None)
        env = {"FERNET_KEY": "", "DATABASE_URL": ""}
        with patch.dict(os.environ, env, clear=False):
            # Remove FERNET_KEY entirely
            os.environ.pop("FERNET_KEY", None)
            from core.models import get_encryption_suite
            import warnings
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                suite = get_encryption_suite()
                assert suite is None
                assert any("SECURITY" in str(warning.message) for warning in w)

    @patch("core.models.st")
    def test_production_without_key_raises(self, mock_st):
        mock_st.secrets.__contains__ = MagicMock(return_value=False)
        mock_st.secrets.__getitem__ = MagicMock(side_effect=KeyError)
        mock_st.secrets.get = MagicMock(return_value=None)
        env = {"DATABASE_URL": "postgresql://host/db"}
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("FERNET_KEY", None)
            from core.models import get_encryption_suite
            with pytest.raises(RuntimeError, match="CRITICAL SECURITY"):
                get_encryption_suite()

    @patch("core.models.st")
    def test_32_byte_raw_key_from_secrets(self, mock_st):
        raw_key = os.urandom(32)
        mock_st.secrets.__getitem__ = MagicMock(return_value=raw_key)
        mock_st.secrets.__contains__ = MagicMock(return_value=False)
        mock_st.secrets.get = MagicMock(return_value=None)
        with patch.dict(os.environ, {"DATABASE_URL": ""}, clear=False):
            os.environ.pop("FERNET_KEY", None)
            from core.models import get_encryption_suite
            suite = get_encryption_suite()
            assert suite is not None
            assert suite.decrypt(suite.encrypt(b"hello")) == b"hello"

    @patch("core.models.st")
    def test_arbitrary_length_key_gets_derived(self, mock_st):
        raw_key = "my-short-key"
        mock_st.secrets.__getitem__ = MagicMock(return_value=raw_key)
        mock_st.secrets.__contains__ = MagicMock(return_value=False)
        mock_st.secrets.get = MagicMock(return_value=None)
        with patch.dict(os.environ, {"DATABASE_URL": ""}, clear=False):
            os.environ.pop("FERNET_KEY", None)
            from core.models import get_encryption_suite
            suite = get_encryption_suite()
            assert suite is not None
            assert suite.decrypt(suite.encrypt(b"test")) == b"test"


class TestEncryptedString:
    def test_encrypt_decrypt_roundtrip(self):
        from cryptography.fernet import Fernet
        key = Fernet.generate_key().decode()
        with patch.dict(os.environ, {"FERNET_KEY": key}, clear=False):
            from core.models import EncryptedString
            td = EncryptedString()
            encrypted = td.process_bind_param("sensitive data", None)
            assert encrypted != "sensitive data"
            decrypted = td.process_result_value(encrypted, None)
            assert decrypted == "sensitive data"

    def test_none_passthrough(self):
        from core.models import EncryptedString
        td = EncryptedString()
        assert td.process_bind_param(None, None) is None
        assert td.process_result_value(None, None) is None

    @patch("core.models.get_encryption_suite", return_value=None)
    def test_dev_mode_no_encryption(self, _mock):
        from core.models import EncryptedString
        td = EncryptedString()
        assert td.process_bind_param("plaintext", None) == "plaintext"
        assert td.process_result_value("plaintext", None) == "plaintext"

    @patch("core.models.get_encryption_suite")
    def test_legacy_plaintext_fallback(self, mock_suite):
        mock_fernet = MagicMock()
        mock_fernet.decrypt.side_effect = Exception("Invalid token")
        mock_suite.return_value = mock_fernet
        from core.models import EncryptedString
        td = EncryptedString()
        assert td.process_result_value("legacy-plain", None) == "legacy-plain"


class TestUserPasswordHashing:
    def test_set_and_check_password(self):
        from core.models import User
        user = User(username="test")
        user.set_password("secure123")
        assert user.password_hash is not None
        assert user.password_hash != "secure123"
        assert user.check_password("secure123") is True
        assert user.check_password("wrong") is False

    def test_different_passwords_different_hashes(self):
        from core.models import User
        u1 = User(username="a")
        u2 = User(username="b")
        u1.set_password("same_password")
        u2.set_password("same_password")
        assert u1.password_hash != u2.password_hash  # bcrypt salts


class TestManagedSession:
    @patch("core.models.Session")
    def test_commits_on_success(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        from core.models import managed_session
        with managed_session() as s:
            s.add("something")
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("core.models.Session")
    def test_rollback_on_exception(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        from core.models import managed_session
        with pytest.raises(ValueError):
            with managed_session():
                raise ValueError("boom")
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


class TestLogAction:
    @patch("core.models.Session")
    def test_creates_audit_log(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        from core.models import log_action
        log_action(1, "test_action", "users", 1, old={"a": 1}, new={"a": 2})
        mock_session.add.assert_called_once()
        added_log = mock_session.add.call_args[0][0]
        assert added_log.action == "test_action"
        assert added_log.user_id == 1

    @patch("core.models.Session")
    def test_none_old_new(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        from core.models import log_action
        log_action(1, "login", "users")
        added_log = mock_session.add.call_args[0][0]
        assert added_log.old_value is None
        assert added_log.new_value is None


class TestCreateDbEngine:
    @patch("core.models.st")
    def test_env_var_takes_priority(self, mock_st):
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///test.db"}):
            from core.models import create_db_engine
            engine = create_db_engine()
            assert "test.db" in str(engine.url)

    @patch("core.models.st")
    def test_postgres_prefix_rewrite(self, mock_st):
        with patch.dict(os.environ, {"DATABASE_URL": "postgres://user:pass@host/db"}):
            from core.models import create_db_engine
            engine = create_db_engine()
            assert str(engine.url).startswith("postgresql://")

    @patch("core.models.st")
    def test_fallback_to_sqlite(self, mock_st):
        mock_st.secrets.__contains__ = MagicMock(return_value=False)
        mock_st.secrets.__getitem__ = MagicMock(side_effect=KeyError)
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DATABASE_URL", None)
            from core.models import create_db_engine
            engine = create_db_engine()
            assert "sqlite" in str(engine.url)


class TestInitDbIfEmpty:
    """The initial admin user is the only way into a fresh production deploy."""

    def _run(self, env):
        """Run init_db_if_empty against an empty in-memory DB, returning created users."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        import core.models as models

        engine = create_engine("sqlite:///:memory:")
        models.Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine)()

        secrets = MagicMock()
        secrets.__contains__ = MagicMock(return_value=False)
        secrets.__getitem__ = MagicMock(side_effect=KeyError)
        secrets.get = MagicMock(return_value=None)

        with patch.object(models, "get_session", return_value=session), \
             patch.object(models, "st", MagicMock(secrets=secrets)), \
             patch.dict(os.environ, env, clear=True):
            models.init_db_if_empty()

        query_session = sessionmaker(bind=engine)()
        return query_session.query(models.User).all()

    def test_admin_password_env_var_creates_admin_in_production(self):
        users = self._run({
            "DATABASE_URL": "postgresql://u:p@h/db",
            "FERNET_KEY": Fernet.generate_key().decode(),
            "ADMIN_PASSWORD": "senha-forte-do-deploy",
        })
        assert len(users) == 1
        assert users[0].username == "atirador_pro"
        assert users[0].check_password("senha-forte-do-deploy")

    def test_production_without_admin_password_creates_nobody(self):
        assert self._run({"DATABASE_URL": "postgresql://u:p@h/db"}) == []

    def test_development_falls_back_to_default_password(self):
        users = self._run({})
        assert len(users) == 1
        assert users[0].check_password("ballistic_admin_2025!")

    def test_env_var_takes_priority_over_default(self):
        users = self._run({"ADMIN_PASSWORD": "sobrescreve-o-padrao"})
        assert users[0].check_password("sobrescreve-o-padrao")
        assert not users[0].check_password("ballistic_admin_2025!")
