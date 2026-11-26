"""Isolated test configuration. Tests never use a developer's database."""

import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-only-signing-key-not-for-real-users-123456"
os.environ["ENVIRONMENT"] = "test"
