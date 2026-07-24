"""Tests for utils.backup_mgr — SQLite backup and rotation."""

import os
import tempfile
import shutil
import pytest
from utils.backup_mgr import run_backup


class TestRunBackup:
    @pytest.fixture(autouse=True)
    def setup_dirs(self, tmp_path):
        self.db_path = str(tmp_path / "test.db")
        self.backup_dir = str(tmp_path / "backups")
        with open(self.db_path, "wb") as f:
            f.write(b"SQLite test data")

    def test_creates_backup_file(self):
        result = run_backup(self.db_path, self.backup_dir)
        assert result is not None
        assert os.path.exists(result)

    def test_backup_content_matches_source(self):
        result = run_backup(self.db_path, self.backup_dir)
        with open(self.db_path, "rb") as src, open(result, "rb") as bak:
            assert src.read() == bak.read()

    def test_creates_backup_dir_if_missing(self):
        assert not os.path.exists(self.backup_dir)
        run_backup(self.db_path, self.backup_dir)
        assert os.path.isdir(self.backup_dir)

    def test_returns_none_if_db_missing(self):
        result = run_backup("/nonexistent/path.db", self.backup_dir)
        assert result is None

    def test_rotation_keeps_limit(self):
        for _ in range(7):
            run_backup(self.db_path, self.backup_dir)
        backups = [f for f in os.listdir(self.backup_dir) if f.startswith("ballistics_backup_")]
        assert len(backups) <= 5

    def test_custom_limit(self):
        for _ in range(5):
            run_backup(self.db_path, self.backup_dir, limit=2)
        backups = [f for f in os.listdir(self.backup_dir) if f.startswith("ballistics_backup_")]
        assert len(backups) <= 2

    def test_backup_filename_format(self):
        result = run_backup(self.db_path, self.backup_dir)
        basename = os.path.basename(result)
        assert basename.startswith("ballistics_backup_")
        assert basename.endswith(".db")
