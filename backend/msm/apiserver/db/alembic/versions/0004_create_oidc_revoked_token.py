"""create oidc_revoked_token table

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-20 10:53:34.000000+00:00

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "oidc_revoked_token",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_email", sa.String(length=150), nullable=False),
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_email"],
            ["user.username"],
            name=op.f("fk_oidc_revoked_token_user_email_user"),
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED",
        ),
        sa.ForeignKeyConstraint(
            ["provider_id"],
            ["oidc_provider.id"],
            name=op.f("fk_oidc_revoked_token_provider_id_oidc_provider"),
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_oidc_revoked_token")),
        sa.UniqueConstraint(
            "token_hash",
            "provider_id",
            name=op.f("uq_oidc_revoked_token_token_hash"),
        ),
    )
    op.create_index(
        op.f("ix_oidc_revoked_token_user_email"),
        "oidc_revoked_token",
        ["user_email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_oidc_revoked_token_provider_id"),
        "oidc_revoked_token",
        ["provider_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_oidc_revoked_token_provider_id"),
        table_name="oidc_revoked_token",
    )
    op.drop_index(
        op.f("ix_oidc_revoked_token_user_email"),
        table_name="oidc_revoked_token",
    )
    op.drop_table("oidc_revoked_token")
