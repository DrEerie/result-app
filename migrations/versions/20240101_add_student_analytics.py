"""Add student analytics table

Revision ID: 20240101_add_student_analytics
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20240101_add_student_analytics'
down_revision = None  # Update this to the actual previous migration
branch_labels = None
depends_on = None


def upgrade():
    # Create enum type for term
    term_type = sa.Enum('First Term', 'Second Term', 'Third Term', 'Annual', 'Half Yearly', name='term_type')
    term_type.create(op.get_bind())
    
    # Create student_analytics table
    op.create_table('student_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('academic_year', sa.String(length=10), nullable=False),
        sa.Column('term', term_type, nullable=False, default='Annual'),
        sa.Column('average_marks', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('rank_in_class', sa.Integer(), nullable=True),
        sa.Column('attendance_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('improvement_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('strengths', sa.ARRAY(sa.String(length=50)), nullable=True),
        sa.Column('weaknesses', sa.ARRAY(sa.String(length=50)), nullable=True),
        sa.Column('recommendations', sa.Text(), nullable=True),
        sa.Column('last_calculated', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'student_id', 'academic_year', 'term')
    )
    
    # Create indexes for performance
    op.create_index(op.f('ix_student_analytics_organization_id'), 'student_analytics', ['organization_id'], unique=False)
    op.create_index(op.f('ix_student_analytics_student_id'), 'student_analytics', ['student_id'], unique=False)
    op.create_index('idx_student_analytics_lookup', 'student_analytics', ['organization_id', 'student_id', 'academic_year', 'term'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index('idx_student_analytics_lookup', table_name='student_analytics')
    op.drop_index(op.f('ix_student_analytics_student_id'), table_name='student_analytics')
    op.drop_index(op.f('ix_student_analytics_organization_id'), table_name='student_analytics')
    
    # Drop table
    op.drop_table('student_analytics')
    
    # Drop enum type
    op.execute('DROP TYPE term_type')