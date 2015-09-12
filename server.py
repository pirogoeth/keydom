#!/usr/bin/env python2.7

from bottle import hook
from datetime import datetime
from rest_api import routing, manager, util
from rest_api.manager import RESTAPIManager
from malibu.util import log, scheduler

from keydom import models

if __name__ == "__main__":

    manager = RESTAPIManager()

    scheduler = scheduler.Scheduler()
    scheduler.save_state("default")

    manager.load_logging()
    log.LoggingDriver.from_config(manager.config.get_section("logging"),
        name = "keydom")
    logger = log.LoggingDriver.find_logger(name = "keydom.__main__")
    models.init_database_from_config(manager.config.get_section("database"))
    manager.load_bottle()
    routing.load_routing_modules(manager, package = "keydom.routes")
    manager.load_dsn()

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
        purge_count = query.execute()


    try:
        manager.run_bottle()
    except:
        manager.dsn.client.captureException()

