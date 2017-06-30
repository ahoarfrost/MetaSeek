"""empty message

Revision ID: c9db57e4805c
Revises: b5ae9c8c6118
Create Date: 2017-06-28 18:11:42.685920

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c9db57e4805c'
down_revision = 'b5ae9c8c6118'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('scrape_error',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uid', sa.String(length=30), nullable=True),
    sa.Column('error_msg', sa.Text(), nullable=True),
    sa.Column('function', sa.String(length=50), nullable=True),
    sa.Column('date_scraped', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('scrape_error')
    # ### end Alembic commands ###