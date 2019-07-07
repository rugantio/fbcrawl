from postgres.settings import postgres_database
from postgres.models import Post

def create_tables():
    postgres_database.drop_tables([Post])
    with postgres_database:
        postgres_database.create_tables([Post])

if __name__ == "__main__":
    create_tables()