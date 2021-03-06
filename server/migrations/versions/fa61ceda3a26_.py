"""empty message

Revision ID: fa61ceda3a26
Revises: 62456de6631f
Create Date: 2017-06-26 16:30:55.536601

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fa61ceda3a26'
down_revision = '62456de6631f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('dataset', sa.Column('date_scraped', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('dataset', 'date_scraped')
    # ### end Alembic commands ###
