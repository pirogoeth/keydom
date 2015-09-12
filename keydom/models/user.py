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

    def schedule_expiry(self):
        """ Schedules token expiration in the scheduler.
        """

        config = manager.RESTAPIManager.get_instance().config.get_section("auth-tokens")

        sch = scheduler.Scheduler(state = "default")
        job = sch.create_job(
            "__delete_token_{}".format(self.timestamp),
            lambda: self.delete_instance(),
            datetime.timedelta(seconds = config.get_int("expire", 14400)),
            recurring = False)

        @job.onfail
        def __expiry_fail(job):
            _log = log.LoggingDriver.find_logger()
            _log.warning("Token expiry failed! user={}, created={}, fired={}"
                .format(
                    self.for_user.username,
                    self.timestamp,
                    self.expire_time))

