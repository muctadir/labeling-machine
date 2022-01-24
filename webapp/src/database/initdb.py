import os
from os import path

from faker import Faker

from src import app
from src.database.models import *
# Registers 'initdb' cli command.
# Usage: `flask initdb`
from src.database.queries.artifact_queries import add_artifacts
from src.helper.tools_common import string_none_or_empty


@app.cli.command('initdb')
def initdb():
    print("Creating non-existing tables ...", end='')
    db.create_all(app=app)  # SQLAlchemy: creates tables defined in `models.py` (only if do not exist)
    print("\t[SUCCESS]")

    initialize_database()
    import_my_data()


def init_users():
    env_pass_key = 'API_PASSWORD'
    password = os.environ.get(env_pass_key)
    if password is None:
        raise ValueError(f'"{env_pass_key}" environment variable for default password is empty.')

    db.session.add(User(username='hossain', password=password, gender='male', education='Masters', occupation='',
                        affiliation='TU/e', years_xp=0))
    db.session.add(User(username='david', password=password, gender='male', education='Masters', occupation='',
                        affiliation='TU/e', years_xp=0))
    db.session.add(User(username='raghav', password=password, gender='male', education='Masters', occupation='',
                        affiliation='TiU', years_xp=0))
    db.session.add(User(username='admin', password=password, gender='male', education='Masters', occupation='',
                        affiliation='TU/e', years_xp=0))
    db.session.commit()


def initialize_database():
    print("Initializing tables with basic data ...", end='')
    init_users()
    print("\t[SUCCESS]")


def import_my_data():
    print("Loading artifacts ...", end='')
    if Artifact.query.count() != 0:
        print("\t[ALREADY DONE]")
        return

    sample_file = './db/sample.txt'
    text = []
    if path.exists(sample_file):
        with open(sample_file) as f:
            for line in f:
                if not string_none_or_empty(line):
                    text.append(line.strip())
    else:
        print(f'No file at {sample_file}. Uploading random value with Faker.', end='')
        fake = Faker()
        text = [fake.paragraph(15) for _ in range(100)]

    add_artifacts(text, 'admin')

    # conn = sqlite3.connect("path/to/data.csv")
    # cursor = conn.cursor()
    # cursor.execute("""SELECT * FROM Artifact;""")
    #
    # for row in cursor:
    #     id = int(row[0])
    #     db.session.add(Artifact(id=id))
    # conn.close()

    print("\t[SUCCESS]")
