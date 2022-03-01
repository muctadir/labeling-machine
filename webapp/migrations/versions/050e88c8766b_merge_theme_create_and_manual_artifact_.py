"""merge theme create and manual artifact upload

Revision ID: 050e88c8766b
Revises: 73b7df31ada5, b3a5f0a9003e
Create Date: 2022-03-01 16:40:10.897575

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '050e88c8766b'
down_revision = ('73b7df31ada5', 'b3a5f0a9003e')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
