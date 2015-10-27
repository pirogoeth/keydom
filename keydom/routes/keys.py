import bottle, json, malibu

from bottle import request, response
from malibu.util import log
from malibu.util.names import get_simple_name
from rest_api import manager, routing
from rest_api.routing.base import api_route

from keydom import models
from keydom.models.key import Key
from keydom.util import ssh_pubkey_fingerprint, token_by_header_data


@routing.routing_module
class KeysAPIRouter(routing.base.APIRouter):
    """ Routes for key specific actions.
    """

    def __init__(self, manager):

        routing.base.APIRouter.__init__(self, manager)

        self.__log = log.LoggingDriver.find_logger()

    @api_route(path = "/key", actions = ["PUT"])
    def key_put():
        """ PUT /key

            Inserts a key into the database. The PUT request should look
            something like this:

              {
                "content": "ssh-rsa ...",
                "short_name": "...",
                "visibility": "public|private|self"
              }
        """

        token = token_by_header_data(request.headers.get("X-Keydom-Session"))

        if not token:
            resp = routing.base.generate_error_response(code = 401)
            resp["message"] = "Invalid authentication token."
            return json.dumps(resp) + "\n"

        if token.has_expired:
            resp = routing.base.generate_error_response(code = 403)
            resp["message"] = "Authentication token has expired. Request another."
            return json.dumps(resp) + "\n"

        user = token.for_user
        key_data = {
            "content": request.forms.get("content") or None,
            "visibility": request.forms.get("visibility") or None,
            "short_name": request.forms.get("short_name") or None,
        }

        if not key_data["content"]:
            resp = routing.base.generate_error_response(code = 400)
            resp["message"] = "Missing PUT request data: 'content'"
            return json.dumps(resp) + "\n"

        if not key_data["short_name"]:
            key_data["short_name"] = get_simple_name()

        if not key_data["visibility"]:
            key_data["visibility"] = "self"

        res = (Key
               .select()
               .where(Key.content == key_data["content"] &
                      Key.short_name == key_data["short_name"] &
                      Key.belongs_to == user))

        if res.count() > 0:
            resp = routing.base.generate_error_response(code = 409)
            resp["message"] = "Key already exists for this user."
            return json.dumps(resp) + "\n"

        new_key = Key.create(
            belongs_to = user,
            **key_data)
        new_key.save()

        try:
            new_key.fingerprint()
        except TypeError as e:
            resp = routing.base.generate_error_response(code = 409)
            resp["message"] = "Invalid key content."
            return json.dumps(resp) + "\n"

        resp = routing.base.generate_bare_response()
        resp["key"] = {
            "short_name": new_key.short_name,
            "fingerprint": new_key.fingerprint(),
            "visibility": new_key.visibility,
        }

        return json.dumps(resp) + "\n"

    @api_route(path = "/key/fingerprint", actions = ["GET"])
    def key_get_fingerprint():
        """ GET /key/fingerprint

            Grabs a key and pulls the fingerprint. Finds the key based on
            short name.

            Accepts the following query parameters:
                user: may be either self, <username>, or [all|any]
                short_name: name of the key
        """

        token = token_by_header_data(request.headers.get("X-Keydom-Session"))

        if not token:
            resp = routing.base.generate_error_response(code = 401)
            resp["message"] = "Invalid authentication token."
            return json.dumps(resp) + "\n"

        if token.has_expired:
            resp = routing.base.generate_error_response(code = 403)
            resp["message"] = "Authentication token has expired. Request another."
            return json.dumps(resp) + "\n"

        key_data = {
            "short_name": request.query.short_name or None,
            "user": request.query.user or token.for_user.username,
        }

        res = (Key
               .select()
               .where(Key.short_name == key_data["short_name"]))

        resp = routing.base.generate_bare_response()
        resp["fingerprints"] = []

        if res.count() == 0:
            return json.dumps(resp) + "\n"

        if key_data["user"].lower() == "self":
            keys = filter(
                lambda key: key.belongs_to.username == token.for_user.username,
                res)
        elif key_data["user"].lower() in ["all", "any"]:
            keys = res
        else:
            keys = filter(
                lambda key: key.belongs_to.username == key_data["user"],
                res)

        for key in keys:
            resp["fingerprints"].append({
                "short_name": key.short_name,
                "owner": key.belongs_to.username,
                "fingerprint": key.fingerprint()
            })

        return json.dumps(resp) + "\n"

