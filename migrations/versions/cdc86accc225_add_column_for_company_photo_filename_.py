"""add column for company photo filename to stock model

Revision ID: cdc86accc225
Revises: c64933c72bb6
Create Date: 2021-08-04 13:10:19.850920

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cdc86accc225'
down_revision = 'c64933c72bb6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('stocks', sa.Column('photo_filename', sa.String(length=256), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('stocks', 'photo_filename')
    # ### end Alembic commands ###
