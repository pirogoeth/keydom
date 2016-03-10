#!/usr/bin/env python2.7

from datetime import datetime
from rest_api import routing
from rest_api.manager import RESTAPIManager
from malibu.util import log, scheduler

from keydom import migrations
from keydom import models


if __name__ == "__main__":

    manager = RESTAPIManager()

    scheduler = scheduler.Scheduler()
    scheduler.save_state("default")

    manager.load_logging()
    log.LoggingDriver.from_config(manager.config.get_section("logging"),
                                  name="keydom")
    logger = log.LoggingDriver.find_logger(name="keydom.__main__")
    models.init_database_from_config(manager.config.get_section("database"))
    manager.load_bottle()
    routing.load_routing_modules(manager, package="keydom.routes")
    manager.load_dsn()

    if "migrate" in manager.arg_parser.options:
        migrations.load_migrations()
        mig_do = manager.arg_parser.options["migrate"]
        if "migrate-script" in manager.arg_parser.options:
            migration_idx = int(manager.arg_parser.options["migrate-script"])
            if mig_do == "upgrade":
                migrations.migrate_single(
                    models.database_migrator,
                    "upgrade",
                    migration_idx)
            elif mig_do == "downgrade":
                migrations.migrate_single(
                    models.database_migrator,
                    "downgrade",
                    migration_idx)
            else:
                log.error("Invalid migration action! Only upgrade or downgrade"
                          " are allowed.")
                exit(1)
            exit(0)
        else:
            if mig_do == "upgrade":
                migrations.migrate_upgrades(models.database_migrator)
            elif mig_do == "downgrade":
                migrations.migrate_downgrades(models.database_migrator)
            else:
                log.error("Invalid migration action! Only upgrade or downgrade"
                          " are allowed.")
                exit(1)
            exit(0)

    # Hooks for the scheduler
    @manager.app.hook("before_request")
    def tick_scheduler():
        """ Ticks the scheduler before a request is processed.
            Should take care of any auth tokens that need to be
            expired.
        """

        scheduler.tick()

    @manager.app.hook("before_request")
    def purge_expired_tokens():
        """ Runs a select on the database to purge expired
            tokens. This exists solely to make sure no expired
            tokens are left over from jobs that got cancelled.
        """

        from keydom.models import user

        query = (user.Token
                 .delete()
                 .where(user.Token.expire_time <= datetime.now()))
        query.execute()

    try:
        manager.run_bottle()
    except:
        manager.dsn.client.captureException()
