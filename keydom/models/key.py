import datetime, peewee
from keydom.models import BaseModel
from keydom.models import user
from keydom.util import ssh_pubkey_fingerprint

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

    def key_type(self):
        """ Returns the key type based on content.
        """

        if "ssh-rsa" in self.content:
            return "ssh-rsa"
        elif "ssh-dsa" in self.content:
            return "ssh-dsa"
        else:
            return "unknown"

    def fingerprint(self):
        """ Returns the fingerprint of the key.
        """

        if self.key_type() in ["ssh-rsa", "ssh-dsa"]:
            return ssh_pubkey_fingerprint(self.content)
        else:
            # Wat.
            return None

