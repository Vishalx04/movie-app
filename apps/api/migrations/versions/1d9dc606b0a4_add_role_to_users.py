"""add role to users

Revision ID: 1d9dc606b0a4
Revises: 08ac3e28fc7e
Create Date: 2026-08-21 17:46:13.093144

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1d9dc606b0a4'
down_revision: Union[str, None] = '08ac3e28fc7e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    userrole = sa.Enum("user", "admin", name="userrole")
    userrole.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "users",
        sa.Column(
            "role",
            userrole,
            nullable=False,
            server_default="user",
        ),
    )

    op.alter_column("users", "role", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "role")

    userrole = sa.Enum("user", "admin", name="userrole")
    userrole.drop(op.get_bind(), checkfirst=True)
