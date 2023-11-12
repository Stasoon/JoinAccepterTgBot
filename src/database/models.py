from peewee import Model, SqliteDatabase, IntegerField, DateTimeField, CharField, BooleanField


db = SqliteDatabase('database.db')


class _BaseModel(Model):
    class Meta:
        database = db


class ReferralLink(_BaseModel):
    class Meta:
        db_table = 'referral_links'

    name = CharField(unique=True)
    user_count = IntegerField(default=0)
    passed_op_count = IntegerField(default=0)


class User(_BaseModel):
    class Meta:
        db_table = 'users'

    name = CharField(default='Пользователь')
    telegram_id = IntegerField(unique=True, null=False)
    registration_timestamp = DateTimeField()
    referral_link = CharField(null=True)


class Admin(_BaseModel):
    class Meta:
        db_table = 'admins'

    telegram_id = IntegerField(unique=True, null=False)
    name = CharField()


class Channel(_BaseModel):
    class Meta:
        db_table = 'channels'

    channel_id = IntegerField()
    title = CharField()
    url = CharField()
    auto_accept = BooleanField(default=True)


def register_models() -> None:
    for model in _BaseModel.__subclasses__():
        model.create_table()
