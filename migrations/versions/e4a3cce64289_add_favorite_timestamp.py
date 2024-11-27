"""add favorite timestamp

Revision ID: e4a3cce64289
Revises: 810876afd61d
Create Date: 2024-10-26 15:11:08.523510

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e4a3cce64289"
down_revision: Union[str, None] = "810876afd61d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "userfavoriteartwork", sa.Column("favorited_at", sa.DateTime(), nullable=False)
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("userfavoriteartwork", "favorited_at")
    # ### end Alembic commands ###
