"""Adopt existing tables and create only tables that are missing.

This baseline supports databases that may already contain tables created by an
older app startup. It deliberately does not alter or drop existing tables.
Future schema changes should be explicit Alembic operations in new revisions.
"""

from alembic import op

from app.database.base import Base
from app.database.models import __all_models__  # noqa: F401 - registers metadata

revision = "0001_safe_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    # checkfirst=True creates only absent tables. It preserves existing tables
    # and their rows; this is safe for adoption of a pre-Alembic database.
    Base.metadata.create_all(bind=bind, checkfirst=True)


def downgrade() -> None:
    # An initial adoption revision must never drop user data. Rollback requires
    # a separately reviewed, explicit migration.
    pass
