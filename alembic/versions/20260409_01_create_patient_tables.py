"""create patient tables

Revision ID: 20260409_01
Revises: None
Create Date: 2026-04-09 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "20260409_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "patients",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("sex", sa.String(length=32), nullable=False),
        sa.Column("contact_email", sa.String(length=255), nullable=False),
        sa.Column("contact_phone", sa.String(length=64), nullable=False),
        sa.Column("blood_group", sa.String(length=16), nullable=True),
        sa.Column("allergies", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "medical_records",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("patient_id", sa.String(length=36), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("record_type", sa.String(length=32), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=512), nullable=False),
        sa.Column("file_url", sa.String(length=2048), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_processed", sa.Boolean(), nullable=False),
        sa.Column("embedding_id", sa.String(length=255), nullable=True),
    )
    op.create_index("ix_medical_records_patient_id", "medical_records", ["patient_id"], unique=False)
    op.create_table(
        "prescriptions",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("patient_id", sa.String(length=36), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("prescribed_by", sa.String(length=255), nullable=False),
        sa.Column("prescribed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("medications", sa.JSON(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_prescriptions_patient_id", "prescriptions", ["patient_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_prescriptions_patient_id", table_name="prescriptions")
    op.drop_table("prescriptions")
    op.drop_index("ix_medical_records_patient_id", table_name="medical_records")
    op.drop_table("medical_records")
    op.drop_table("patients")

