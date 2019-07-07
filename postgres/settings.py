from playhouse.pool import PooledPostgresqlExtDatabase
from dotenv import load_dotenv
import os
load_dotenv()

POSTGRESQL_SETTINGS = {
    'DATABASE': os.getenv("POSTGRESQL_SETTINGS_DATABASE"),
    'USER': os.getenv("POSTGRESQL_SETTINGS_USER"),
    'HOST': os.getenv("POSTGRESQL_SETTINGS_HOST"),
    'PORT': os.getenv("POSTGRESQL_SETTINGS_PORT"),
    'PASSWORD': os.getenv("POSTGRESQL_SETTINGS_PASSWORD")
}

DEFAULT_LOCALE = 'en'

TIMEZONE = os.getenv("TIMEZONE")

postgres_database = PooledPostgresqlExtDatabase(
    POSTGRESQL_SETTINGS['DATABASE'],
    user=POSTGRESQL_SETTINGS['USER'],
    host=POSTGRESQL_SETTINGS['HOST'],
    port=POSTGRESQL_SETTINGS['PORT'],
    password=POSTGRESQL_SETTINGS['PASSWORD'],
    max_connections=8,
    stale_timeout=300,
    register_hstore=False,
    )