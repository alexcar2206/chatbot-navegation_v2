"""Add declaracion_borrador table

Revision ID: a7b8c9d0e1f2
Revises: d4c1a8e37b62
Create Date: 2026-10-29 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'a7b8c9d0e1f2'
down_revision: str | None = 'd4c1a8e37b62'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'declaracion_borrador' not in inspector.get_table_names():
        op.create_table(
            'declaracion_borrador',
            sa.Column('id', sa.Text(), primary_key=True),
            sa.Column('user_id', sa.Text(), nullable=False),
            sa.Column('nombre', sa.Text(), nullable=False),
            sa.Column('paso', sa.Integer(), nullable=False),
            sa.Column('datos', sa.JSON(), nullable=True),
            sa.Column('version', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.BigInteger(), nullable=False),
            sa.Column('updated_at', sa.BigInteger(), nullable=False),
        )

    indices = {ix['name'] for ix in sa.inspect(conn).get_indexes('declaracion_borrador')}
    if 'ix_declaracion_borrador_user_id' not in indices:
        op.create_index('ix_declaracion_borrador_user_id', 'declaracion_borrador', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_declaracion_borrador_user_id', table_name='declaracion_borrador')
    op.drop_table('declaracion_borrador')
