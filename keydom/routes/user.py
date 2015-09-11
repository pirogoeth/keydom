import bottle, hashlib, json, malibu

from bottle import request, response
from rest_api import manager, routing
from rest_api.routing.base import api_route

from keydom import models
from keydom.models.user import User


class UserAPIRouter(routing.base.APIRouter):
    """ Routes for user specific actions, such as registration,
        authentication, etc.
    """

    def __init__(self, manager):

        routing.base.APIRouter.__init__(self, manager)

    @api_route(path = "/user/list", actions = ["GET"])
    def user_list():
        """ GET /user/list

            Returns a JSON list of all the users registered
            in the database.
        """

        users = []
        for user in User.select():
            users.append(user.username)

        resp = routing.base.generate_bare_response()
        resp.update({"users": users})

        yield json.dumps(resp) + "\n"

    @api_route(path = "/user/register", actions = ["POST"])
    def user_register():
        """ POST /user/register

            Attempts to register a username for use. Returns
            `status: 200` if success, or these values on failure:
                `status: 409` - if username is taken
        """

        username = request.forms.get("username")
        password = request.forms.get("password")
        email = request.forms.get("email")

        res = User.select().where(
            (User.username == username) | (User.email == email))

        if res.count() != 0:
            resp = routing.base.generate_error_response(code = 409)
            resp["message"] = "Username taken."
            return json.dumps(resp) + "\n"

        password = hashlib.sha512(password).hexdigest()

        new_user = User.create(
            username = username,
            password = password,
            email = email)
        new_user.save()

        resp = routing.base.generate_bare_response()
        resp["info"] = {
            "registered": True,
            "username": username,
            "email": email
        }

        return json.dumps(resp) + "\n"


register_route_providers = [UserAPIRouter]
