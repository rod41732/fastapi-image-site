"""user like artwork table

Revision ID: 0d7d8634930c
Revises: 2dd66c6361b3
Create Date: 2024-10-26 14:17:26.708506

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0d7d8634930c"
down_revision: Union[str, None] = "2dd66c6361b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "userlikeartwork",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("artwork_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["artwork_id"],
            ["artwork.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("user_id", "artwork_id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("userlikeartwork")
    # ### end Alembic commands ###
