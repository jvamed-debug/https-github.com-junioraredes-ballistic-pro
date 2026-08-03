"""Regressoes de seguranca.

Todas rodam com FERNET_KEY configurada — o estado de producao. As falhas que
elas cobrem eram invisiveis em modo dev, porque sem chave a cifra e desligada,
o email vai em texto claro e as buscas funcionam. Os bugs so abriam com a
cifra ativa, exatamente onde os testes nao olhavam.
"""

import os
import importlib

import pytest
from cryptography.fernet import Fernet


@pytest.fixture()
def prod_db(tmp_path, monkeypatch):
    """Um banco limpo com criptografia PII ligada, recarregando core.models
    para que o engine aponte para o arquivo temporario."""
    db_path = tmp_path / "sec.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("FERNET_KEY", Fernet.generate_key().decode())

    import core.models as models
    importlib.reload(models)
    import core.auth as auth
    importlib.reload(auth)

    models.Base.metadata.create_all(models.engine)
    models.ensure_schema_compliance(models.engine)
    yield models, auth


class TestEmailUniqueness:
    """A coluna email e cifrada de forma nao-deterministica, entao a constraint
    unique dela nunca dispara e `email == x` nunca casa. A unicidade e a busca
    ficam no blind index; sem ele, duplicatas passavam batido em producao."""

    def test_duplicate_email_is_rejected(self, prod_db):
        _, auth = prod_db
        ok1, _ = auth.register_user("alice", "senha1234", "Alice", "12345678900", "dup@example.com", None)
        ok2, msg = auth.register_user("bob", "senha1234", "Bob", "98765432100", "dup@example.com", None)
        assert ok1 is True
        assert ok2 is False

    def test_duplicate_email_is_case_insensitive(self, prod_db):
        _, auth = prod_db
        auth.register_user("alice", "senha1234", "Alice", "12345678900", "dup@example.com", None)
        ok, _ = auth.register_user("bob", "senha1234", "Bob", "98765432100", "DUP@EXAMPLE.COM", None)
        assert ok is False

    def test_only_one_row_persists_for_a_duplicate(self, prod_db):
        models, auth = prod_db
        auth.register_user("alice", "senha1234", "Alice", "12345678900", "dup@example.com", None)
        auth.register_user("bob", "senha1234", "Bob", "98765432100", "dup@example.com", None)
        with models.managed_session() as db:
            assert db.query(models.User).count() == 1

    def test_distinct_emails_are_allowed(self, prod_db):
        _, auth = prod_db
        assert auth.register_user("alice", "senha1234", "Alice", "12345678900", "a@example.com", None)[0]
        assert auth.register_user("bob", "senha1234", "Bob", "98765432100", "b@example.com", None)[0]

    def test_multiple_users_without_email_are_allowed(self, prod_db):
        """NULLs nao colidem numa constraint unique — cadastro sem email deve
        seguir permitido para varios usuarios."""
        _, auth = prod_db
        assert auth.register_user("alice", "senha1234", "Alice", None, None, None)[0]
        assert auth.register_user("bob", "senha1234", "Bob", None, None, None)[0]


class TestPasswordRecoveryFindsUsers:
    def test_recovery_locates_the_user_by_email(self, prod_db):
        models, auth = prod_db
        auth.register_user("alice", "senha1234", "Alice", "12345678900", "alice@example.com", None)
        auth.recover_password("alice@example.com")
        with models.managed_session() as db:
            found = db.query(models.AuditLog).filter_by(action="auth_recovery_requested").count()
        assert found == 1

    def test_recovery_message_is_generic_regardless(self, prod_db):
        """Anti-enumeracao: mesma resposta exista o usuario ou nao."""
        _, auth = prod_db
        _, hit = auth.recover_password("alice@example.com")
        auth.register_user("alice", "senha1234", "Alice", "12345678900", "alice@example.com", None)
        _, miss = auth.recover_password("naoexiste@example.com")
        _, present = auth.recover_password("alice@example.com")
        assert hit == miss == present


class TestBlindIndex:
    def test_is_deterministic(self, prod_db):
        models, _ = prod_db
        assert models.blind_index("x@y.com") == models.blind_index("x@y.com")

    def test_normalizes_case_and_whitespace(self, prod_db):
        models, _ = prod_db
        assert models.blind_index("  X@Y.COM ") == models.blind_index("x@y.com")

    def test_empty_and_none_are_none(self, prod_db):
        models, _ = prod_db
        assert models.blind_index(None) is None
        assert models.blind_index("") is None
        assert models.blind_index("   ") is None

    def test_is_not_reversible_to_plaintext(self, prod_db):
        """O hash nao pode conter o texto claro."""
        models, _ = prod_db
        assert "x@y.com" not in models.blind_index("x@y.com")

    def test_stays_in_sync_on_attribute_update(self, prod_db):
        """Trocar o email por atribuicao (como faz o Perfil) tem de recalcular
        o hash pelo evento, senao a busca voltaria a falhar apos uma edicao."""
        models, _ = prod_db
        with models.managed_session() as db:
            u = models.User(username="alice", email="old@example.com")
            u.set_password("senha1234")
            db.add(u)
        with models.managed_session() as db:
            u = db.query(models.User).filter_by(username="alice").first()
            u.email = "new@example.com"
        with models.managed_session() as db:
            by_new = db.query(models.User).filter(
                models.User.email_hash == models.blind_index("new@example.com")
            ).first()
            by_old = db.query(models.User).filter(
                models.User.email_hash == models.blind_index("old@example.com")
            ).first()
        assert by_new is not None
        assert by_old is None


class TestLoginLockout:
    def test_lockout_after_threshold(self, prod_db):
        _, auth = prod_db
        for _ in range(auth.LOCKOUT_THRESHOLD):
            auth.record_failed_login("victim")
        assert auth.login_lock_remaining("victim") > 0

    def test_below_threshold_is_not_locked(self, prod_db):
        _, auth = prod_db
        for _ in range(auth.LOCKOUT_THRESHOLD - 1):
            auth.record_failed_login("victim")
        assert auth.login_lock_remaining("victim") == 0

    def test_untried_identifier_is_free(self, prod_db):
        _, auth = prod_db
        assert auth.login_lock_remaining("stranger") == 0

    def test_lockout_is_per_identifier(self, prod_db):
        _, auth = prod_db
        for _ in range(auth.LOCKOUT_THRESHOLD):
            auth.record_failed_login("alice")
        assert auth.login_lock_remaining("alice") > 0
        assert auth.login_lock_remaining("bob") == 0

    def test_success_clears_the_counter(self, prod_db):
        _, auth = prod_db
        for _ in range(auth.LOCKOUT_THRESHOLD):
            auth.record_failed_login("alice")
        auth.clear_login_attempts("alice")
        assert auth.login_lock_remaining("alice") == 0

    def test_lockout_survives_a_new_session(self, prod_db):
        """O ponto todo: o bloqueio vive no banco, nao em st.session_state.
        Recarregar o modulo de auth (uma 'nova sessao') nao o zera."""
        models, auth = prod_db
        for _ in range(auth.LOCKOUT_THRESHOLD):
            auth.record_failed_login("alice")
        importlib.reload(auth)
        assert auth.login_lock_remaining("alice") > 0

    def test_blank_identifier_records_nothing(self, prod_db):
        models, auth = prod_db
        auth.record_failed_login("")
        auth.record_failed_login(None)
        with models.managed_session() as db:
            assert db.query(models.LoginAttempt).count() == 0


class TestCpfNormalization:
    def test_cpf_is_stored_as_digits_only(self, prod_db):
        models, auth = prod_db
        auth.register_user("alice", "senha1234", "Alice", "111.222.333-44", "a@example.com", None)
        with models.managed_session() as db:
            u = db.query(models.User).filter_by(username="alice").first()
            cpf = u.cpf  # dentro da sessao: EncryptedString decifra ao ler
        assert cpf == "11122233344"
