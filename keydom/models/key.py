import datetime, peewee
from keydom.models import BaseModel
from keydom.models import user


class Key(BaseModel):

    belongs_to = ForeignKeyField(user.User)
    content = CharField()
    published_at = DateTimeField(default = datetime.datetime.now)

    class Meta:
        order_by = ('belongs_to', 'published_at',)
