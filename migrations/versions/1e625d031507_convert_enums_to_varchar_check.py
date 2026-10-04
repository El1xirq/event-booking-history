"""convert enums to varchar+check

Revision ID: xxxx
Revises: a53606ea9f71
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1e625d031507"
down_revision: Union[str, Sequence[str], None] = "9a318ff6e505"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ─── users.role ───────────────────────────────────────
    op.add_column(
        "users",
        sa.Column("role_new", sa.String(20), nullable=False, server_default="customer"),
    )
    op.execute("UPDATE users SET role_new = lower(role::text)")
    op.drop_column("users", "role")
    op.alter_column("users", "role_new", new_column_name="role")
    op.execute(
        "ALTER TABLE users ADD CONSTRAINT ck_users_role "
        "CHECK (role IN ('customer', 'organizer', 'admin')) NOT VALID"
    )
    op.execute("ALTER TABLE users VALIDATE CONSTRAINT ck_users_role")
    op.execute("DROP TYPE IF EXISTS user_role")

    # ─── reservations.status ─────────────────────────────
    op.add_column(
        "reservations",
        sa.Column("status_new", sa.String(20), nullable=False, server_default="pending"),
    )
    op.execute("UPDATE reservations SET status_new = lower(status::text)")
    op.drop_column("reservations", "status")
    op.alter_column("reservations", "status_new", new_column_name="status")
    op.execute(
        "ALTER TABLE reservations ADD CONSTRAINT ck_reservations_status "
        "CHECK (status IN ('pending', 'confirmed', 'cancelled', 'expired')) NOT VALID"
    )
    op.execute("ALTER TABLE reservations VALIDATE CONSTRAINT ck_reservations_status")
    op.execute("DROP TYPE IF EXISTS reservation_status")

    # ─── events.status ───────────────────────────────────
    op.add_column(
        "events",
        sa.Column("status_new", sa.String(20), nullable=False, server_default="draft"),
    )
    op.execute("UPDATE events SET status_new = lower(status::text)")
    op.drop_column("events", "status")
    op.alter_column("events", "status_new", new_column_name="status")
    op.execute(
        "ALTER TABLE events ADD CONSTRAINT ck_events_status "
        "CHECK (status IN ('draft', 'published', 'cancelled', 'finished')) NOT VALID"
    )
    op.execute("ALTER TABLE events VALIDATE CONSTRAINT ck_events_status")
    op.execute("DROP TYPE IF EXISTS event_status")

    # ─── seats.seat_type ─────────────────────────────────
    op.add_column(
        "seats",
        sa.Column("seat_type_new", sa.String(20), nullable=False, server_default="standard"),
    )
    op.execute("UPDATE seats SET seat_type_new = lower(seat_type::text)")
    op.drop_column("seats", "seat_type")
    op.alter_column("seats", "seat_type_new", new_column_name="seat_type")
    op.execute(
        "ALTER TABLE seats ADD CONSTRAINT ck_seats_seat_type "
        "CHECK (seat_type IN ('standard', 'vip')) NOT VALID"
    )
    op.execute("ALTER TABLE seats VALIDATE CONSTRAINT ck_seats_seat_type")
    op.execute("DROP TYPE IF EXISTS seat_type")


def downgrade() -> None:
    """No downgrade — enums were removed intentionally."""
    pass
