"""Add column pokemon.unclaimed_from_hack.

Revision ID: 2e2e77fd15a
Revises: 3e91c95c5c1
Create Date: 2013-12-23 17:14:17.045898

"""

# revision identifiers, used by Alembic.
revision = '2e2e77fd15a'
down_revision = '3e91c95c5c1'

from alembic import op
import sqlalchemy as sa

def upgrade():
    pokemon = sa.sql.table('pokemon',
        sa.Column('unclaimed_from_hack', sa.Boolean)
    )

    op.add_column('pokemon', sa.Column('unclaimed_from_hack', sa.Boolean()))

    # I'm too lazy to figure out how to actually set this in Alembic
    op.execute(pokemon.update().values({'unclaimed_from_hack': op.inline_literal(True)}))
    op.alter_column('pokemon', 'unclaimed_from_hack', nullable=False)


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('pokemon', 'unclaimed_from_hack')
    ### end Alembic commands ###
