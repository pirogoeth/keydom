import hashlib
import json

from bottle import request
from malibu.util import log
from rest_api import manager, routing
from rest_api.routing.base import api_route
from validate_email import validate_email

from keydom.models.user import Token, User
from keydom.util import token_by_header_data


@routing.routing_module
class UserAPIRouter(routing.base.APIRouter):
    """ Routes for user specific actions, such as registration,
        authentication, etc.
    """

    def __init__(self, manager):

        routing.base.APIRouter.__init__(self, manager)

        self.__log = log.LoggingDriver.find_logger()

    @api_route(path="/users",
               actions=["GET"],
               returns="application/json")
    def user_list():
        """ GET /users

            Returns a JSON list of all the users registered
            in the database.
        """

        users = []
        for user in User.select():
            users.append(user.username)

        resp = routing.base.generate_bare_response()
        resp.update({"users": users})

        yield json.dumps(resp) + "\n"

    @api_route(path="/register",
               actions=["POST"],
               returns="application/json")
    def user_register():
        """ POST /register

            Attempts to register a username for use. Returns
            `status: 200` if success, or these values on failure:
                `status: 409` - if username is taken
        """

        username = request.forms.get("username")
        password = request.forms.get("password")
        email = request.forms.get("email")

        res = (User
               .select()
               .where((User.username == username) | (User.email == email)))

        if res.count() > 0:
            resp = routing.base.generate_error_response(code=409)
            resp["message"] = "Username taken."
            return json.dumps(resp) + "\n"

        if not validate_email(email):
            resp = routing.base.generate_error_response(code=409)
            resp["message"] = "Invalid email address."
            return json.dumps(resp) + "\n"

        password = hashlib.sha512(password).hexdigest()

        new_user = User.create(
            username=username,
            password=password,
            email=email)
        new_user.save()

        resp = routing.base.generate_bare_response()
        resp["account"] = {
            "registered": True,
            "username": username,
            "email": email
        }

        return json.dumps(resp) + "\n"

    @api_route(path="/auth",
               actions=["POST"],
               returns="application/json")
    def user_auth():
        """ POST /auth

            Takes a user's username and password and attempts to auth
            against the database. If there is a match, it will return
            `status: 200` and an auth token to use for future operations.
            Note that the auth token expires after a set amount of time.
        """

        config = manager.RESTAPIManager.get_instance().config.get_section("auth-tokens")

        username = request.forms.get("username")
        password = hashlib.sha512(request.forms.get("password")).hexdigest()

        try:
            res = User.get(User.username == username, User.password == password)
        except Exception:
            resp = routing.base.generate_error_response(code=409)
            resp["message"] = "Invalid username or password."
            return json.dumps(resp) + "\n"

        token = res.create_token()

        resp = routing.base.generate_bare_response()
        resp["username"] = username
        resp["auth"] = {
            "token": token.token,
            "expires": config.get_int("expire", 14400),
        }

        return json.dumps(resp) + "\n"

    @api_route(path="/session",
               actions=["GET"],
               returns="application/json")
    def user_session():
        """ GET /session

            Headers:
              X-Keydom-Session => current session token

            Reads the X-Keydom-Session header and checks if the token is valid.
            If it is, the API returns the username that the token is
            associated with.
        """

        auth_token = request.headers.get("X-Keydom-Session")

        if not auth_token:
            resp = routing.base.generate_error_response(code=409)
            resp["message"] = "Invalid authentication token."
            return json.dumps(resp) + "\n"

        try:
            token = Token.get(Token.token == auth_token)
        except Exception:
            resp = routing.base.generate_error_response(code=409)
            resp["message"] = "Invalid authentication token."
            return json.dumps(resp) + "\n"

        user = token.for_user

        if token.has_expired:
            resp = routing.base.generate_error_response(code=403)
            resp["message"] = "Authentication token has expired. Request another."
            return json.dumps(resp) + "\n"

        resp = routing.base.generate_bare_response()
        resp["session"] = {
            "username": user.username,
        }
        resp["token"] = {
            "expires_at": str(token.expire_time),
            "created_at": str(token.timestamp),
        }

        return json.dumps(resp) + "\n"

    @api_route(path="/user/<username>",
               actions=['GET'],
               returns="application/json")
    def user_info(username):
        """ GET /user/:username

            Headers:
              X-Keydom-Session => current session token

            Returns information about a user. Some information will
            only be returned if a valid session token is provided.
        """

        token = token_by_header_data(request.headers.get("X-Keydom-Session"))

        if token is not None and token.has_expired:
            token = None

        try:
            user = User.get(User.username == username)
        except Exception:
            resp = routing.base.generate_error_response(code=404)
            resp["message"] = "Invalid username."
            return json.dumps(resp) + "\n"

        resp = routing.base.generate_bare_response()
        resp["user"] = {
            "username": user.username,
            "join_date": str(user.join_date),
        }

        if token:
            # Information for registered users is inserted here.
            resp["user"].update({
                "email": user.email,
            })

        return json.dumps(resp) + "\n"

    @api_route(path="/tokens",
               actions=['GET'],
               returns="application/json")
    def user_tokens():
        """ GET /tokens

            Headers:
              X-Keydom-Session => current session token

            Returns the list of tokens that are active for the user
            associated with the current token.
        """

        auth_token = request.headers.get("X-Keydom-Session")

        if not auth_token:
            resp = routing.base.generate_error_response(code=409)
            resp["message"] = "Invalid authentication token."
            return json.dumps(resp) + "\n"

        try:
            token = Token.get(Token.token == auth_token)
        except Exception:
            resp = routing.base.generate_error_response(code=409)
            resp["message"] = "Invalid authentication token."
            return json.dumps(resp) + "\n"

        if token.has_expired:
            resp = routing.base.generate_error_response(code=403)
            resp["message"] = "Authentication token has expired. Request another."
            return json.dumps(resp) + "\n"

        user = token.for_user
        tokens = user.tokens()

        resp = routing.base.generate_bare_response()
        resp["session"] = {
            "username": user.username,
        }
        resp["tokens"] = []

        for user_token in tokens:
            resp["tokens"].append({
                "token": str(token.token),
                "expires_at": str(token.expire_time),
                "created_at": str(token.timestamp),
            })

        return json.dumps(resp) + "\n"
