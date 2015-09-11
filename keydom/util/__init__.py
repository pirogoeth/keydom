import urlparse


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
