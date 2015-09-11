import bottle, json, malibu

from bottle import request, response
from rest_api import manager, routing
from rest_api.routing.base import api_route

from keydom import models


class UserAPIRouter(routing.base.APIRouter):
    """ Routes for user specific actions, such as registration,
        authentication, etc.
    """

    def __init__(self, manager):

        routing.base.APIRouter.__init__(self, manager)

    @api_route(path = "/users", actions = ["GET"])
    def user_list():
        """ GET /users

            Returns a JSON list of all the users registered
            in the database.
        """

        users = []
        for user in models.user.User.select():
            users.append(user.username)

        resp = routing.base.generate_bare_response()
        resp.update({"users": users})

        yield json.dumps(resp) + "\n"

