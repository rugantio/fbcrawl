from peewee import *
from postgres.settings import postgres_database, TIMEZONE
from datetime import datetime
from pytz import timezone


def timezone_now():
    return datetime.now().replace(tzinfo=timezone(TIMEZONE))

class Post(Model):
    post_id = CharField(unique=True, index=True)
    source = CharField()
    date = DateField(index=True)
    text = TextField()
    url = CharField(unique=True)
    shared_in = CharField()

    reactions = IntegerField(default=0)
    likes = IntegerField(default=0)
    ahah = IntegerField(default=0)
    love = IntegerField(default=0)
    wow = IntegerField(default=0)
    sigh = IntegerField(default=0)
    grr = IntegerField(default=0)
    comment_count = IntegerField(default=0)
    inserted = DateTimeField(default=timezone_now)

    class Meta:
        database = postgres_database

