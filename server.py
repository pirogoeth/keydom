#!/usr/bin/env python2.7

from rest_api import routing, manager, util
from rest_api.manager import RESTAPIManager
from malibu.util import log


if __name__ == "__main__":

    manager = RESTAPIManager()
    manager.load_logging()
    log.LoggingDriver.from_config(manager.config.get_section("logging"),
        name = "keydom")
    log = log.LoggingDriver.find_logger(name = "keydom.__main__")
    manager.load_bottle()
    routing.load_routing_modules(manager, package = "keydom.routes")
    manager.load_dsn()
    try:
        manager.run_bottle()
    except:
        manager.dsn.client.captureException()

