import datetime
from peewee import Model, CharField, BigIntegerField, DateTimeField, ForeignKeyField, BooleanField, TextField, FloatField, IntegerField
from database.connection import db

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    telegram_id = BigIntegerField(primary_key=True)
    username = CharField(null=True)
    first_name = CharField(null=True)
    role = CharField(default="General User")  # Investor, Analyst, Founder, Finance Professional, Student, etc.
    onboarding_status = CharField(default="not_started")  # not_started, in_progress, completed
    onboarding_step = IntegerField(default=0)
    created_at = DateTimeField(default=datetime.datetime.now)

class UserPreference(BaseModel):
    user = ForeignKeyField(User, backref="preferences", unique=True)
    briefing_time = CharField(default="08:30")  # HH:MM
    notification_enabled = BooleanField(default=True)
    interests = TextField(default="Technology, Finance")  # Comma separated
    briefing_scope = TextField(default="market_news,watchlist_updates")

class Watchlist(BaseModel):
    user = ForeignKeyField(User, backref="watchlist")
    ticker = CharField()  # e.g., AAPL, TSLA
    added_at = DateTimeField(default=datetime.datetime.now)
    alert_price_high = FloatField(null=True)
    alert_price_low = FloatField(null=True)

    class Meta:
        indexes = (
            (('user', 'ticker'), True),  # Composite unique index
        )

class ConversationHistory(BaseModel):
    user = ForeignKeyField(User, backref="history")
    sender = CharField()  # user or assistant
    content = TextField()
    media_type = CharField(default="text")  # text, voice, image
    timestamp = DateTimeField(default=datetime.datetime.now)

def init_db():
    db.connect(reuse_if_open=True)
    db.create_tables([User, UserPreference, Watchlist, ConversationHistory])
    db.close()

if __name__ == "__main__":
    init_db()
    print("Database tables initialized successfully.")
