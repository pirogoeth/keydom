import datetime, peewee
from keydom.models import BaseModel


class User(BaseModel):

    username = peewee.CharField(unique = True)
    password = peewee.CharField()
    email = peewee.CharField()
    join_date = peewee.DateTimeField(default = datetime.datetime.now)

    class Meta:
        order_by = ('username',)


class UserRelationship(BaseModel):

    from_user = ForeignKeyField(User, related_name = 'following')
    to_user = ForeignKeyField(User, related_name = 'followers')

    class Meta:
        indexes = (
            (('from_user', 'to_user'), True),
        )

