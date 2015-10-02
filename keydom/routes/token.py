import bottle, hashlib, json, malibu

from bottle import request, response
from malibu.util import log
from rest_api import manager, routing
from rest_api.routing.base import api_route
from validate_email import validate_email

from keydom import models
from keydom.models.user import Token, User


class TokenAPIRouter(routing.base.APIRouter):
    """ Routing for token specific operations, such as
        revocation, validation, etc.
    """

    def __init__(self, manager):

        routing.base.APIRouter.__init__(self, manager)

    @api_route(path = "/token/check", actions = ["POST"])
    def token_check():
        """ POST /token/check

            Checks if the token that is posted is active
            and returns the associated username.
        """

        token = request.forms.get("token")

        try: res = Token.get(Token.token == token)
        except:
            resp = routing.base.generate_error_response(code = 409)
            resp["message"] = "Invalid token."
            return json.dumps(resp) + "\n"

        resp = routing.base.generate_bare_response()
        resp["auth"] = {
            "username": res.for_user.username,
            "expires_at": str(res.expire_time),
        }

        return json.dumps(resp) + "\n"


register_route_providers = [TokenAPIRouter]
