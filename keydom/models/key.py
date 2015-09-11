import datetime, peewee
from keydom.models import BaseModel
from keydom.models import user


class Key(BaseModel):

    belongs_to = peewee.ForeignKeyField(user.User)
    content = peewee.CharField()
    published_at = peewee.DateTimeField(default = datetime.datetime.now)

    class Meta:
        order_by = ('belongs_to', 'published_at',)

