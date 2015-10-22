import base64, binascii, hashlib, random, urlparse


def ssh_pubkey_fingerprint(key):
    """ Generates a key fingerprint for an SSH public key.
    """

    key = base64.b64decode(key.strip().split()[1].encode('ascii'))
    md5_fp = hashlib.md5(key).hexdigest()

    return ':'.join(a + b for a, b in zip(md5_fp[::2], md5_fp[1::2]))


def generate_random_token(length = 64):
    """ Generates a random token of specified length.
    """

    lrange = 16 ** length
    hexval = "%0{}x".format(length)
    return hexval % (random.randrange(lrange))


def token_by_header_data(auth_token):
    """ Accepts the user provided auth token and returns a
        token object if the token is valid, otherwise, None.
    """

    from keydom.models.user import Token

    if not auth_token:
        return None

    try: token = Token.get(Token.token == auth_token)
    except Exception as e:
        return None

    return token


def parse_uri(uri):
    """ This implies that we are passed a uri that looks something like:
          proto://username:password@hostname:port/database

        In most cases, you can omit the port and database from the string:
          proto://username:password@hostname

        Also, in cases with no username, you can omit that:
          proto://:password@hostname:port/database

        Also supports additional arguments:
          proto://hostname:port/database?arg1=val&arg2=vals
    """

    proto = uri.split('://')[0]
    uri = uri.split('://')[1]

    _host = uri.split('@')[-1]
    _host = _host.split(':')
    if len(_host) == 2:
        host = _host[0]
        if '/' in _host[1]:
            port = int(_host[1].split('/')[0])
        else:
            port = int(_host[1])
    else:
        host = _host[0]
        if '/' in host:
            host = host.split('/')[0]
        port = None

    if "@" in uri:
        _cred = uri[0:uri.rfind(':'.join(_host)) - 1]
        _cred = _cred.split(':')
        if len(_cred) == 2:
            _user = _cred[0]
            _pass = _cred[1]
        else:
            _user = _cred[0]
            _pass = None
    else:
        _user = None
        _pass = None

    database = uri.split('/')
    if len(database) >= 2:
        database = database[1]
        if '?' in database:
            _db = database.split('?')
            database = _db[0]
            args = urlparse.parse_qs(_db[1], keep_blank_values = True)
        else:
            args = None
    else:
        database = None
        args = None

    return {
        "protocol": proto,
        "resource": uri,
        "host": host,
        "port": port,
        "username": _user,
        "password": _pass,
        "database": database,
        "args": args,
        "uri": "{}://{}".format(proto, uri)}
