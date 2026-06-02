"""initial schema

Revision ID: 202606020001
Revises:
Create Date: 2026-06-02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "202606020001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    payment_type = postgresql.ENUM("hourly", "shift", "fixed", name="payment_type", create_type=False)
    user_role = postgresql.ENUM("admin", "manager", "viewer", name="telegram_user_role", create_type=False)
    payment_type.create(op.get_bind(), checkfirst=True)
    user_role.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("payment_type", payment_type, nullable=False),
        sa.Column("hourly_rate", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_employees_full_name", "employees", ["full_name"])

    op.create_table(
        "telegram_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("role", user_role, nullable=False, server_default="manager"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_telegram_users_telegram_id", "telegram_users", ["telegram_id"])

    op.create_table(
        "timesheet_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("hours_worked", sa.Numeric(6, 2), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("employee_id", "work_date", name="uq_timesheet_employee_date"),
    )
    op.create_index("ix_timesheet_entries_employee_id", "timesheet_entries", ["employee_id"])
    op.create_index("ix_timesheet_entries_work_date", "timesheet_entries", ["work_date"])


def downgrade() -> None:
    op.drop_table("timesheet_entries")
    op.drop_table("telegram_users")
    op.drop_index("ix_employees_full_name", table_name="employees")
    op.drop_table("employees")
    sa.Enum(name="telegram_user_role").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="payment_type").drop(op.get_bind(), checkfirst=True)
