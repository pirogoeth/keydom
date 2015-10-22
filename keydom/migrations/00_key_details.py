import datetime, peewee
from playhouse.migrate import migrate
from malibu.util.names import get_simple_name

from keydom import migrations


@migrations.upgrade
def create_key_details(migrator):
    """ Modifies the Key table to add several columns:
          short_name text indexed not null
          visibility text not null
    """

    short_name = peewee.CharField(
        default = get_simple_name(),
        index = True,
        unique = False,
        null = False)

    visibility = peewee.CharField(
        default = "self",
        null = False,
        choices = [
            ('self', 'self',),
            ('private', 'private',),
            ('public', 'public',)
        ])

    migrate(
        migrator.add_column('key', 'short_name', short_name),
        migrator.add_column('key', 'visibility', visibility)
    )


@migrations.downgrade
def drop_key_details(migrator):
    """ Modifies the Key table to drop the columns created by
        create_key_details.
    """

    migrate(
        migrator.drop_column('key', 'short_name'),
        migrator.drop_column('key', 'visibility')
    )

