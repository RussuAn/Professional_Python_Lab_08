"""Initial schema for groups/students, before email column."""
from alembic import op
import sqlalchemy as sa
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("groups", sa.Column("id", sa.Integer, primary_key=True),
                    sa.Column("name", sa.String(50), nullable=False), sa.UniqueConstraint("name"))
    op.create_table("students", sa.Column("id", sa.Integer, primary_key=True),
                    sa.Column("first_name", sa.String(100), nullable=False),
                    sa.Column("last_name", sa.String(100), nullable=False),
                    sa.Column("average_grade", sa.Float, nullable=False),
                    sa.Column("group_id", sa.Integer, sa.ForeignKey("groups.id", ondelete="RESTRICT"), nullable=False),
                    sa.CheckConstraint("average_grade >= 0 AND average_grade <= 100", name="valid_grade"))

def downgrade() -> None:
    op.drop_table("students")
    op.drop_table("groups")
