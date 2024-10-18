"""user_test_string

Revision ID: 7e3b2fbc8026
Revises: 66462fcf5309
Create Date: 2024-10-17 17:09:17.071101

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "7e3b2fbc8026"
down_revision: Union[str, None] = "66462fcf5309"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "user",
        sa.Column(
            "test_string",
            sqlmodel.sql.sqltypes.AutoString(),
            server_default="some-string",
            nullable=False,
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("user", "test_string")
    # ### end Alembic commands ###
