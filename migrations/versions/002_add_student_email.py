"""Add nullable unique email field to students (requested migration)."""
from alembic import op
import sqlalchemy as sa
revision = "002_email"
down_revision = "001_initial"
branch_labels = None
depends_on = None

def upgrade() -> None:
    with op.batch_alter_table("students") as batch_op:
        batch_op.add_column(sa.Column("email", sa.String(255), nullable=True))
        batch_op.create_unique_constraint("uq_student_email", ["email"])

def downgrade() -> None:
    with op.batch_alter_table("students") as batch_op:
        batch_op.drop_constraint("uq_student_email", type_="unique")
        batch_op.drop_column("email")
