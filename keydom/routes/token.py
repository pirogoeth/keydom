import json

from bottle import request
from rest_api import routing
from rest_api.routing.base import api_route
from malibu.util import log

from keydom.models.user import Token


@routing.routing_module
class TokenAPIRouter(routing.base.APIRouter):
    """ Routing for token specific operations, such as
        revocation, validation, etc.
    """

    def __init__(self, manager):

        routing.base.APIRouter.__init__(self, manager)

        self.__log = log.LoggingDriver.find_logger()

    @api_route(path="/token/check",
               actions=["POST"],
               returns="application/json")
    def token_check():
        """ POST /token/check

            Checks if the token that is posted is active
            and returns the associated username.
        """

        token = request.forms.get("token")

        try:
            res = Token.get(Token.token == token)
        except:
            resp = routing.base.generate_error_response(code=409)
            resp["message"] = "Invalid authentication token."
            return json.dumps(resp) + "\n"

        resp = routing.base.generate_bare_response()

        if res.has_expired:
            resp["expired"] = True

        resp["auth"] = {
            "username": res.for_user.username,
            "expires_at": str(res.expire_time),
        }

        return json.dumps(resp) + "\n"

    @api_route(path="/token/revoke",
               actions=["POST"],
               returns="application/json")
    def token_revoke():
        """ POST /token/revoke

            Expires the token that is currently being used.
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

        token.expire()

        resp = routing.base.generate_bare_response()
        return json.dumps(resp) + "\n"

    @api_route(path="/token/revoke/all",
               actions=["POST"],
               returns="application/json")
    def token_revoke_all():
        """ POST /token/revoke/all

            Expires ALL tokens for the user represented by the posted token.
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
        resp["tokens"] = {}

        for user_token in tokens:
            try:
                user_token.expire()
            except:
                pass

            resp["tokens"].update({
                user_token.token: {
                    "status": "revoked"
                }})

        return json.dumps(resp) + "\n"
