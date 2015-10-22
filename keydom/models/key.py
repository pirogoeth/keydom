import datetime, peewee
from keydom.models import BaseModel
from keydom.models import user


class Key(BaseModel):

    belongs_to = peewee.ForeignKeyField(user.User)
    content = peewee.CharField()
    published_at = peewee.DateTimeField(default = datetime.datetime.now)
    short_name = peewee.CharField(
        index = True,
        unique = False,
        null = False)
    visibility = peewee.CharField(
        default = "self",
        null = False,
        choices = [
            ('self', 'self',),
            ('private', 'private',),
            ('public', 'public',)
        ])

    class Meta:
        order_by = ('belongs_to', 'published_at', 'short_name',)

