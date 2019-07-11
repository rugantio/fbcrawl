from postgres.settings import postgres_database
from postgres.models import Post, Group

def create_tables():
    postgres_database.drop_tables([Group])
    with postgres_database:
        postgres_database.create_tables([Group])

if __name__ == "__main__":
    create_tables()