import glob, os
from keydom.util import parse_uri
import peewee, playhouse

modules = glob.glob(os.path.dirname(__file__) + "/*.py")
__all__ = [os.path.basename(f)[:-3] for f in modules if not os.path.basename(f).startswith('_') and not f.endswith('__init__.py') and os.path.isfile(f)]


database_proxy = peewee.Proxy()

class FKSqliteDatabase(peewee.SqliteDatabase):
    """ A simple wrapper around peewee's SqliteDatabase that
        enables foreign keys with a pragma when the connection
        is initialized.
    """

    def initialize_connection(self, conn):

        self.execute_sql("PRAGMA foreign_keys=ON;")


class BaseModel(peewee.Model):
    """ Simple base model with the database set as a peewee
        database proxy so we can dynamically initialize the
        database connection with information from the config
        file.
    """

    class Meta:
        database = database_proxy


def init_database_from_config(db_config):
    """ Takes a malibu ConfigurationSection object to create
        the database connection accordingly.
    """

    if db_config is None:
        raise ValueError("Config section 'database' does not exist!")

    db_uri = db_config.get_string("uri", None)
    if db_uri is None:
        raise ValueError("Config value database.uri can not be empty!")

    db_uri = parse_uri(db_uri)

    if db_uri["protocol"] == "sqlite":
        print db_uri["resource"]
        database = FKSqliteDatabase(db_uri["resource"])
    elif db_uri["protocol"] == "postgres":
        database = playhouse.postgres_ext.PostgresqlExtDatabase(
            db_uri["database"],
            user = db_uri["username"],
            password = db_uri["password"],
            host = db_uri["host"],
            port = db_uri["port"])
    elif db_uri["protocol"] == "mysql":
        database = peewee.MySQLDatabase(
            db_uri["database"],
            user = db_uri["username"],
            password = db_uri["password"],
            host = db_uri["host"],
            port = db_uri["port"])
    else:
        raise ValueError("Unknown DB protocol: %s" % (db_uri["protocol"]))

    database_proxy.initialize(database)
    database.connect()

