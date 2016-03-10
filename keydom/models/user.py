import datetime, peewee

from malibu.util import log, scheduler
from rest_api import manager

from keydom.models import BaseModel
from keydom.util import generate_random_token


class User(BaseModel):

    username = peewee.CharField(unique = True)
    password = peewee.CharField()
    email = peewee.CharField(unique = True)
    join_date = peewee.DateTimeField(default = datetime.datetime.now)

    class Meta:
        order_by = ('username',)

    def create_token(self):
        """ Creates an auth token for the user.
        """

        config = manager.RESTAPIManager.get_instance().config.get_section("auth-tokens")
        expiry = (datetime.datetime.now() +
                  datetime.timedelta(
                      seconds = config.get_int("expire", 14400)))
        token_size = config.get_int("size", 64)

        token = Token(
            for_user = self,
            token = generate_random_token(length = token_size),
            expire_time = expiry)

        token.schedule_expiry()
        token.save()

        return token

    def tokens(self):
        """ Returns all tokens that are assigned to this user.
        """

        return (Token
                .select()
                .where(Token.for_user == self))

    def keys(self):
        """ Returns all keys that belong to this user.
        """

        from keydom.models import key  # Import `key` here to prevent cycdep

        return (key.Key
                .select()
                .where(key.Key.belongs_to == self))

    def scoped_keys(self, scope="public"):
        """ Returns user keys which are visible from a given scope.
            The "public" scope can only see public visibility keys.
            The "private" scope can see both public and private vis keys.
            The "self" scope is only applied to the user's own profile and
              allows the user to see all "public", "private", and "self" keys.
        """

        if scope not in ["public", "private", "self"]:
            raise ValueError("scope must be one of: public, private, self")

        keys = []

        if scope is "public":
            keys = filter(
                self.keys(),
                lambda k: k.visibility in ["public"])
        elif scope is "private":
            keys = filter(
                self.keys(),
                lambda k: k.visibility in ["public", "private"])
        elif scope is "self":
            keys = self.keys()

        return keys

    def following(self):
        """ Returns all users this user is following.
        """

        return (User
                .select()
                .join(UserRelationship, on = UserRelationship.to_user)
                .where(UserRelationship.from_user == self))

    def followers(self):
        """ Returns all users that are following this user.
        """

        return (User
                .select()
                .join(UserRelationship, on = UserRelationship.from_user)
                .where(UserRelationship.to_user == self))

    def is_friend(self, user):
        """ Returns a boolean if the following statements are true:
             - :user: is in following
             - :user: is in followers
        """

        return user in self.following() and user in self.followers()


class UserRelationship(BaseModel):

    from_user = peewee.ForeignKeyField(User, related_name = 'following')
    to_user = peewee.ForeignKeyField(User, related_name = 'followers')

    class Meta:
        indexes = (
            (('from_user', 'to_user'), True),
        )


class Token(BaseModel):

    for_user = peewee.ForeignKeyField(User, related_name = "owner")
    timestamp = peewee.DateTimeField(default = datetime.datetime.now)
    expire_time = peewee.DateTimeField()
    token = peewee.CharField(default = generate_random_token)

    class Meta:
        order_by = ('for_user',)
        indexes = (
            (('for_user',), False),
        )

    @property
    def has_expired(self):
        """ Checks to see if the token has expired or not.
        """

        config = manager.RESTAPIManager.get_instance().config.get_section("auth-tokens")

        if not self.expire_time:
            self.expire_time = self.timestamp + datetime.timedelta(
                seconds = config.get_int("expire", 14400))

        return self.expire_time <= datetime.datetime.now()

    def expire(self, kill_job = True):
        """ Expires a token immediately.
        """

        _log = log.LoggingDriver.find_logger()

        if kill_job:
            # Kill the expiry job.
            try:
                sch = scheduler.Scheduler(state = "default")
                job_name = "__expire_token_{}".format(self.timestamp)
                sch.remove_job(job_name)
            except Exception as e:
                _log.warning("An error was encountered while trying to kill "
                             "expiry job: %s" % (str(e)))
                manager.RESTAPIManager.get_instance().dsn.client.captureException()

        # Set the expire time to now.
        self.expire_time = datetime.datetime.now()
        self.save()

    def schedule_expiry(self):
        """ Schedules token expiration in the scheduler.
        """

        config = manager.RESTAPIManager.get_instance().config.get_section("auth-tokens")

        self.expire_time = self.timestamp + datetime.timedelta(
            seconds = config.get_int("expire", 14400))

        sch = scheduler.Scheduler(state = "default")
        job = sch.create_job(
            "__expire_token_{}".format(self.timestamp),
            lambda: self.expire(kill_job = False),
            datetime.timedelta(seconds = config.get_int("expire", 14400)),
            recurring = False)

        @job.onfail
        def __expiry_fail(job):
            manager.RESTAPIManager.get_instance().dsn.client.captureException()
            _log = log.LoggingDriver.find_logger()
            _log.warning("Token expiry failed! user={}, created={}, fired={}"
                .format(
                    self.for_user.username,
                    self.timestamp,
                    self.expire_time))

